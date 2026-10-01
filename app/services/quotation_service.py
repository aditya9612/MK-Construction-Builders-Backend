from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationFailedError
from app.core.logging import get_logger
from app.models.company import CompanySettings
from app.models.enums import QuotationStatus
from app.models.quotation import Quotation
from app.models.quotation_items import (
    QuotationAdditionalItem,
    QuotationConstructionItem,
    QuotationDoor,
    QuotationElectricalItem,
    QuotationGranite,
    QuotationMaterial,
    QuotationPainting,
    QuotationPlumbingItem,
    QuotationTerm,
    QuotationTile,
    QuotationWindow,
)
from app.models.user import User
from app.repositories.customer_repository import CustomerRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.quotation_repository import QuotationRepository
from app.schemas.common import PaginatedData
from app.schemas.company import CompanySettingsOut
from app.schemas.quotation import (
    CalculationSummary,
    QuotationCreate,
    QuotationListItem,
    QuotationOut,
    QuotationUpdate,
)
from app.services.audit_service import AuditService
from app.services.calculation_service import CalculationService, window_area_and_amount
from app.utils.calculations import money
from app.utils.pagination import paginate
from app.utils.quotation_number import generate_quotation_number

logger = get_logger(__name__)


class QuotationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = QuotationRepository(session)
        self.customers = CustomerRepository(session)
        self.projects = ProjectRepository(session)
        self.calc = CalculationService()
        self.audit = AuditService(session)

    async def _company(self) -> CompanySettings:
        company = (await self.session.execute(select(CompanySettings).limit(1))).scalar_one_or_none()
        if not company:
            raise ValidationFailedError("Company settings are not configured")
        return company

    async def _validate_customer_project(self, customer_id: int, project_id: int):
        customer = await self.customers.get(customer_id)
        if not customer or not customer.is_active:
            raise ValidationFailedError("Customer not found or inactive")
        project = await self.projects.get(project_id)
        if not project:
            raise ValidationFailedError("Project not found")
        if project.customer_id != customer_id:
            raise ValidationFailedError("Project does not belong to the selected customer")
        return customer, project

    def _assert_gst(self, gst_percentage: Decimal) -> None:
        if gst_percentage > Decimal(str(settings.max_gst_percentage)):
            raise ValidationFailedError(
                f"GST percentage cannot exceed {settings.max_gst_percentage}"
            )

    def _assert_editable(self, quotation: Quotation, allow_revision: bool = False) -> None:
        if quotation.status == QuotationStatus.APPROVED and not allow_revision:
            raise ConflictError("Approved quotations cannot be modified. Duplicate to create a revision.")
        if quotation.status == QuotationStatus.EXPIRED:
            raise ConflictError("Expired quotations cannot be modified")

    def _build_items(self, quotation: Quotation, payload: QuotationCreate) -> CalculationSummary:
        quotation.construction_items.clear()
        quotation.additional_items.clear()
        quotation.electrical_items.clear()
        quotation.plumbing_items.clear()
        quotation.doors.clear()
        quotation.windows.clear()
        quotation.tiles.clear()
        quotation.granite.clear()
        quotation.painting.clear()
        quotation.materials.clear()
        quotation.terms.clear()

        for item in payload.construction_items:
            amount = self.calc.calculate_item_amount(item.quantity, item.rate)
            quotation.construction_items.append(
                QuotationConstructionItem(
                    rate_master_id=item.rate_master_id,
                    description=item.description,
                    quantity=money(item.quantity),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=amount,
                    sort_order=item.sort_order,
                )
            )
        for item in payload.additional_items:
            quotation.additional_items.append(
                QuotationAdditionalItem(
                    category=item.category,
                    description=item.description,
                    quantity=money(item.quantity),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.quantity, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.electrical_items:
            quotation.electrical_items.append(
                QuotationElectricalItem(
                    area=item.area,
                    item_name=item.item_name,
                    quantity=money(item.quantity),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.quantity, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.plumbing_items:
            quotation.plumbing_items.append(
                QuotationPlumbingItem(
                    item_name=item.item_name,
                    quantity=money(item.quantity),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.quantity, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.doors:
            quotation.doors.append(
                QuotationDoor(
                    item_id=item.item_id,
                    item_name=item.item_name,
                    quantity=money(item.quantity),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.quantity, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.windows:
            area, amount = window_area_and_amount(item.length, item.width, item.rate)
            quotation.windows.append(
                QuotationWindow(
                    item_id=item.item_id,
                    item_name=item.item_name,
                    length=money(item.length),
                    width=money(item.width),
                    area=area,
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=amount,
                    sort_order=item.sort_order,
                )
            )
        for item in payload.tiles:
            quotation.tiles.append(
                QuotationTile(
                    item_id=item.item_id,
                    category=item.category,
                    description=item.description,
                    area=money(item.area),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.area, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.granite:
            quotation.granite.append(
                QuotationGranite(
                    item_id=item.item_id,
                    category=item.category,
                    description=item.description,
                    area=money(item.area),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.area, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.painting:
            quotation.painting.append(
                QuotationPainting(
                    category=item.category,
                    description=item.description,
                    area=money(item.area),
                    unit=item.unit,
                    rate=money(item.rate),
                    amount=self.calc.calculate_item_amount(item.area, item.rate),
                    sort_order=item.sort_order,
                )
            )
        for item in payload.materials:
            quotation.materials.append(
                QuotationMaterial(
                    material_id=item.material_id,
                    name=item.name,
                    category=item.category,
                    brand=item.brand,
                    specification=item.specification,
                    unit=item.unit,
                    sort_order=item.sort_order,
                )
            )
        for item in payload.terms:
            quotation.terms.append(
                QuotationTerm(
                    term_id=item.term_id,
                    term_order=item.term_order,
                    custom_content=item.custom_content,
                )
            )

        summary = self.calc.summarize(
            construction=self.calc.calculate_construction_total(quotation.construction_items),
            additional=self.calc.calculate_additional_total(quotation.additional_items),
            electrical=self.calc.calculate_electrical_total(quotation.electrical_items),
            plumbing=self.calc.calculate_plumbing_total(quotation.plumbing_items),
            doors=self.calc.calculate_door_total(quotation.doors),
            windows=self.calc.calculate_window_total(quotation.windows),
            tiles=self.calc.calculate_tile_total(quotation.tiles),
            granite=self.calc.calculate_granite_total(quotation.granite),
            painting=self.calc.calculate_painting_total(quotation.painting),
            discount_percentage=payload.discount_percentage,
            gst_percentage=payload.gst_percentage,
        )
        quotation.subtotal = summary.subtotal
        quotation.discount_percentage = summary.discount_percentage
        quotation.discount_amount = summary.discount_amount
        quotation.taxable_amount = summary.taxable_amount
        quotation.gst_percentage = summary.gst_percentage
        quotation.gst_amount = summary.gst_amount
        quotation.grand_total = summary.grand_total
        return summary

    def _to_out(self, quotation: Quotation, summary: CalculationSummary | None = None) -> QuotationOut:
        data = QuotationOut.model_validate(quotation)
        data.calculation_summary = summary or self.calc.summarize(
            construction=self.calc.calculate_construction_total(quotation.construction_items),
            additional=self.calc.calculate_additional_total(quotation.additional_items),
            electrical=self.calc.calculate_electrical_total(quotation.electrical_items),
            plumbing=self.calc.calculate_plumbing_total(quotation.plumbing_items),
            doors=self.calc.calculate_door_total(quotation.doors),
            windows=self.calc.calculate_window_total(quotation.windows),
            tiles=self.calc.calculate_tile_total(quotation.tiles),
            granite=self.calc.calculate_granite_total(quotation.granite),
            painting=self.calc.calculate_painting_total(quotation.painting),
            discount_percentage=quotation.discount_percentage,
            gst_percentage=quotation.gst_percentage,
        )
        return data

    async def create(self, payload: QuotationCreate, user: User) -> QuotationOut:
        self._assert_gst(payload.gst_percentage)
        await self._validate_customer_project(payload.customer_id, payload.project_id)
        company = await self._company()
        quotation = Quotation(
            quotation_number=await generate_quotation_number(self.session, company.quotation_prefix),
            customer_id=payload.customer_id,
            project_id=payload.project_id,
            quotation_date=payload.quotation_date,
            status=QuotationStatus.DRAFT,
            notes=payload.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        self._build_items(quotation, payload)
        await self.repo.add(quotation)
        await self.audit.log(
            user_id=user.id,
            action="quotation.created",
            entity_type="quotation",
            entity_id=quotation.id,
            new_data={"quotation_number": quotation.quotation_number, "grand_total": str(quotation.grand_total)},
        )
        await self.session.commit()
        detailed = await self.repo.get_detailed(quotation.id)
        logger.info("quotation_created %s", quotation.quotation_number)
        return self._to_out(detailed)

    async def update(self, quotation_id: int, payload: QuotationUpdate, user: User) -> QuotationOut:
        self._assert_gst(payload.gst_percentage)
        quotation = await self.repo.get_detailed(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        self._assert_editable(quotation)
        await self._validate_customer_project(payload.customer_id, payload.project_id)
        old = {"grand_total": str(quotation.grand_total), "status": quotation.status}
        quotation.customer_id = payload.customer_id
        quotation.project_id = payload.project_id
        quotation.quotation_date = payload.quotation_date
        quotation.notes = payload.notes
        quotation.updated_by = user.id
        self._build_items(quotation, payload)
        await self.audit.log(
            user_id=user.id,
            action="quotation.updated",
            entity_type="quotation",
            entity_id=quotation.id,
            old_data=old,
            new_data={"grand_total": str(quotation.grand_total)},
        )
        await self.session.commit()
        detailed = await self.repo.get_detailed(quotation.id)
        logger.info("quotation_updated %s", quotation.quotation_number)
        return self._to_out(detailed)

    async def get(self, quotation_id: int) -> QuotationOut:
        quotation = await self.repo.get_detailed(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        return self._to_out(quotation)

    async def list(self, **filters) -> PaginatedData[QuotationListItem]:
        page = filters.pop("page")
        page_size = filters.pop("page_size")
        items, data = await paginate(self.session, self.repo.list_query(**filters), page, page_size)
        return PaginatedData(
            items=[QuotationListItem.model_validate(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def delete(self, quotation_id: int, user: User) -> None:
        quotation = await self.repo.get(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.status == QuotationStatus.APPROVED:
            raise ForbiddenError("Approved quotations cannot be deleted")
        if quotation.status != QuotationStatus.DRAFT and user.role.name not in ("ADMIN", "MANAGER"):
            raise ForbiddenError("Only draft quotations can be deleted by this role")
        await self.audit.log(
            user_id=user.id,
            action="quotation.deleted",
            entity_type="quotation",
            entity_id=quotation.id,
            old_data={"quotation_number": quotation.quotation_number},
        )
        await self.session.delete(quotation)
        await self.session.commit()
        logger.info("quotation_deleted %s", quotation.quotation_number)

    async def duplicate(self, quotation_id: int, user: User) -> QuotationOut:
        source = await self.repo.get_detailed(quotation_id)
        if not source:
            raise NotFoundError("Quotation not found")
        company = await self._company()
        clone = Quotation(
            quotation_number=await generate_quotation_number(self.session, company.quotation_prefix),
            customer_id=source.customer_id,
            project_id=source.project_id,
            quotation_date=source.quotation_date,
            status=QuotationStatus.DRAFT,
            notes=source.notes,
            created_by=user.id,
            updated_by=user.id,
            discount_percentage=source.discount_percentage,
            gst_percentage=source.gst_percentage,
        )
        for item in source.construction_items:
            clone.construction_items.append(
                QuotationConstructionItem(
                    rate_master_id=item.rate_master_id,
                    description=item.description,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.additional_items:
            clone.additional_items.append(
                QuotationAdditionalItem(
                    category=item.category,
                    description=item.description,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.electrical_items:
            clone.electrical_items.append(
                QuotationElectricalItem(
                    area=item.area,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.plumbing_items:
            clone.plumbing_items.append(
                QuotationPlumbingItem(
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.doors:
            clone.doors.append(
                QuotationDoor(
                    item_id=item.item_id,
                    item_name=item.item_name,
                    quantity=item.quantity,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.windows:
            clone.windows.append(
                QuotationWindow(
                    item_id=item.item_id,
                    item_name=item.item_name,
                    length=item.length,
                    width=item.width,
                    area=item.area,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.tiles:
            clone.tiles.append(
                QuotationTile(
                    item_id=item.item_id,
                    category=item.category,
                    description=item.description,
                    area=item.area,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.granite:
            clone.granite.append(
                QuotationGranite(
                    item_id=item.item_id,
                    category=item.category,
                    description=item.description,
                    area=item.area,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.painting:
            clone.painting.append(
                QuotationPainting(
                    category=item.category,
                    description=item.description,
                    area=item.area,
                    unit=item.unit,
                    rate=item.rate,
                    amount=item.amount,
                    sort_order=item.sort_order,
                )
            )
        for item in source.materials:
            clone.materials.append(
                QuotationMaterial(
                    material_id=item.material_id,
                    name=item.name,
                    category=item.category,
                    brand=item.brand,
                    specification=item.specification,
                    unit=item.unit,
                    sort_order=item.sort_order,
                )
            )
        for item in source.terms:
            clone.terms.append(
                QuotationTerm(
                    term_id=item.term_id,
                    term_order=item.term_order,
                    custom_content=item.custom_content,
                )
            )
        clone.subtotal = source.subtotal
        clone.discount_amount = source.discount_amount
        clone.taxable_amount = source.taxable_amount
        clone.gst_amount = source.gst_amount
        clone.grand_total = source.grand_total
        await self.repo.add(clone)
        await self.audit.log(
            user_id=user.id,
            action="quotation.duplicated",
            entity_type="quotation",
            entity_id=clone.id,
            old_data={"source_id": source.id},
            new_data={"quotation_number": clone.quotation_number},
        )
        await self.session.commit()
        detailed = await self.repo.get_detailed(clone.id)
        return self._to_out(detailed)

    async def change_status(
        self,
        quotation_id: int,
        new_status: QuotationStatus,
        user: User,
        allowed_from: set[str],
        action: str,
    ) -> QuotationOut:
        quotation = await self.repo.get_detailed(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.status not in {str(s) for s in allowed_from}:
            raise ConflictError(f"Cannot {action} a quotation in {quotation.status} status")
        old_status = quotation.status
        quotation.status = str(new_status)
        quotation.updated_by = user.id
        await self.audit.log(
            user_id=user.id,
            action=f"quotation.{action}",
            entity_type="quotation",
            entity_id=quotation.id,
            old_data={"status": old_status},
            new_data={"status": str(new_status)},
        )
        await self.session.commit()
        logger.info("quotation_%s %s", action, quotation.quotation_number)
        detailed = await self.repo.get_detailed(quotation.id)
        return self._to_out(detailed)

    async def send(self, quotation_id: int, user: User) -> QuotationOut:
        return await self.change_status(
            quotation_id, QuotationStatus.SENT, user, {QuotationStatus.DRAFT}, "send"
        )

    async def approve(self, quotation_id: int, user: User) -> QuotationOut:
        return await self.change_status(
            quotation_id,
            QuotationStatus.APPROVED,
            user,
            {QuotationStatus.SENT, QuotationStatus.DRAFT},
            "approve",
        )

    async def reject(self, quotation_id: int, user: User) -> QuotationOut:
        return await self.change_status(
            quotation_id,
            QuotationStatus.REJECTED,
            user,
            {QuotationStatus.SENT, QuotationStatus.DRAFT},
            "reject",
        )

    async def expire(self, quotation_id: int, user: User) -> QuotationOut:
        return await self.change_status(
            quotation_id,
            QuotationStatus.EXPIRED,
            user,
            {QuotationStatus.DRAFT, QuotationStatus.SENT},
            "expire",
        )

    async def summary(self, quotation_id: int) -> CalculationSummary:
        quotation = await self.repo.get_detailed(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        return self._to_out(quotation).calculation_summary

    async def preview(self, quotation_id: int) -> dict:
        quotation = await self.repo.get_detailed(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        company = await self._company()
        out = self._to_out(quotation)
        terms = []
        for row in quotation.terms:
            title = row.term.title if row.term else "Custom term"
            content = row.custom_content or (row.term.content if row.term else "")
            terms.append({"term_order": row.term_order, "title": title, "content": content})
        return {
            "company": CompanySettingsOut.model_validate(company).model_dump(),
            "customer": out.customer.model_dump() if out.customer else None,
            "project": out.project.model_dump() if out.project else None,
            "quotation": {
                "id": out.id,
                "quotation_number": out.quotation_number,
                "quotation_date": out.quotation_date.isoformat(),
                "status": out.status,
                "notes": out.notes,
            },
            "construction": [i.model_dump() for i in out.construction_items],
            "additional": [i.model_dump() for i in out.additional_items],
            "electrical": [i.model_dump() for i in out.electrical_items],
            "plumbing": [i.model_dump() for i in out.plumbing_items],
            "doors": [i.model_dump() for i in out.doors],
            "windows": [i.model_dump() for i in out.windows],
            "tiles": [i.model_dump() for i in out.tiles],
            "granite": [i.model_dump() for i in out.granite],
            "painting": [i.model_dump() for i in out.painting],
            "materials": [i.model_dump() for i in out.materials],
            "terms": terms,
            "summary": out.calculation_summary.model_dump() if out.calculation_summary else None,
            "signature": company.signature_url,
        }
