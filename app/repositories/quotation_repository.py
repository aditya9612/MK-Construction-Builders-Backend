from datetime import date
from decimal import Decimal

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.customer import Customer
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.quotation_items import QuotationTerm


DETAIL_OPTIONS = (
    selectinload(Quotation.customer),
    selectinload(Quotation.project),
    selectinload(Quotation.construction_items),
    selectinload(Quotation.additional_items),
    selectinload(Quotation.electrical_items),
    selectinload(Quotation.plumbing_items),
    selectinload(Quotation.doors),
    selectinload(Quotation.windows),
    selectinload(Quotation.tiles),
    selectinload(Quotation.granite),
    selectinload(Quotation.painting),
    selectinload(Quotation.materials),
    selectinload(Quotation.terms).selectinload(QuotationTerm.term),
)


class QuotationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, quotation_id: int) -> Quotation | None:
        return await self.session.get(Quotation, quotation_id)

    async def get_detailed(self, quotation_id: int) -> Quotation | None:
        stmt = select(Quotation).options(*DETAIL_OPTIONS).where(Quotation.id == quotation_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def list_query(
        self,
        search: str | None = None,
        status: str | None = None,
        customer_id: int | None = None,
        project_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select:
        stmt = (
            select(Quotation)
            .options(joinedload(Quotation.customer), joinedload(Quotation.project))
            .join(Customer, Quotation.customer_id == Customer.id)
            .join(Project, Quotation.project_id == Project.id)
        )
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Quotation.quotation_number.ilike(like),
                    Customer.name.ilike(like),
                    Customer.mobile.ilike(like),
                    Project.project_name.ilike(like),
                    Project.site_address.ilike(like),
                )
            )
        if status:
            stmt = stmt.where(Quotation.status == status)
        if customer_id is not None:
            stmt = stmt.where(Quotation.customer_id == customer_id)
        if project_id is not None:
            stmt = stmt.where(Quotation.project_id == project_id)
        if date_from:
            stmt = stmt.where(Quotation.quotation_date >= date_from)
        if date_to:
            stmt = stmt.where(Quotation.quotation_date <= date_to)
        if min_amount is not None:
            stmt = stmt.where(Quotation.grand_total >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Quotation.grand_total <= max_amount)
        column = getattr(Quotation, sort_by, Quotation.created_at)
        stmt = stmt.order_by(column.asc() if sort_order == "asc" else column.desc())
        return stmt

    async def add(self, quotation: Quotation) -> Quotation:
        self.session.add(quotation)
        await self.session.flush()
        return quotation
