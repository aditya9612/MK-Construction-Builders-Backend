"""Website enquiry intake and admin follow-up."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, TooManyRequestsError
from app.models.cms_enums import EnquiryStatus
from app.models.enquiry import WebsiteEnquiry
from app.repositories.enquiry_repository import RATE_LIMIT_MAX, RATE_LIMIT_WINDOW, EnquiryRepository
from app.schemas.common import PaginatedData
from app.schemas.enquiry import (
    EnquiryAdminUpdate,
    EnquiryCreate,
    EnquiryListItem,
    EnquiryOut,
    EnquiryPublicOut,
    EnquiryUnreadCount,
    message_preview,
)
from app.utils.pagination import paginate


def _to_out(item: WebsiteEnquiry) -> EnquiryOut:
    return EnquiryOut.model_validate(item)


def _to_list_item(item: WebsiteEnquiry) -> EnquiryListItem:
    return EnquiryListItem(
        id=item.id,
        name=item.name,
        mobile=item.mobile,
        email=item.email,
        project_type=item.project_type,
        location=item.location,
        construction_area=item.construction_area,
        message_preview=message_preview(item.message),
        status=item.status,
        is_read=item.is_read,
        created_at=item.created_at,
    )


class EnquiryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EnquiryRepository(session)

    async def create_public(
        self,
        payload: EnquiryCreate,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> EnquiryPublicOut:
        since = datetime.now(timezone.utc) - RATE_LIMIT_WINDOW
        recent = await self.repo.recent_count_for_mobile(payload.mobile, since=since)
        if recent >= RATE_LIMIT_MAX:
            raise TooManyRequestsError("Please wait before submitting again.")

        item = WebsiteEnquiry(
            name=payload.name,
            mobile=payload.mobile,
            email=str(payload.email) if payload.email else None,
            project_type=payload.project_type,
            location=payload.location,
            construction_area=payload.construction_area,
            message=payload.message,
            status=EnquiryStatus.NEW.value,
            is_read=False,
            source="WEBSITE",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.repo.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return EnquiryPublicOut(id=item.id, created_at=item.created_at)

    async def unread_count(self) -> EnquiryUnreadCount:
        return EnquiryUnreadCount(unread_count=await self.repo.unread_count())

    async def list_admin(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        status: object | None = None,
        is_read: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> PaginatedData[EnquiryListItem]:
        status_val = status.value if hasattr(status, "value") else status
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                search=search,
                status=status_val,
                is_read=is_read,
                date_from=date_from,
                date_to=date_to,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            page,
            page_size,
        )
        return PaginatedData(
            items=[_to_list_item(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def get_admin(self, enquiry_id: int, *, mark_read: bool = True) -> EnquiryOut:
        item = await self.repo.get(enquiry_id)
        if not item:
            raise NotFoundError("Enquiry not found")
        if mark_read and not item.is_read:
            item.is_read = True
            if item.status == EnquiryStatus.NEW.value:
                item.status = EnquiryStatus.READ.value
            await self.session.commit()
            await self.session.refresh(item)
        return _to_out(item)

    async def update(self, enquiry_id: int, payload: EnquiryAdminUpdate) -> EnquiryOut:
        item = await self.repo.get(enquiry_id)
        if not item:
            raise NotFoundError("Enquiry not found")
        data = payload.model_dump(exclude_unset=True)
        if "status" in data and data["status"] is not None:
            value = data["status"]
            item.status = value.value if hasattr(value, "value") else value
            if item.status == EnquiryStatus.SPAM.value:
                item.is_read = True
        if "admin_notes" in data:
            item.admin_notes = data["admin_notes"]
        if "is_read" in data and data["is_read"] is not None:
            item.is_read = data["is_read"]
        await self.session.commit()
        await self.session.refresh(item)
        return _to_out(item)

    async def mark_unread(self, enquiry_id: int) -> EnquiryOut:
        item = await self.repo.get(enquiry_id)
        if not item:
            raise NotFoundError("Enquiry not found")
        item.is_read = False
        await self.session.commit()
        await self.session.refresh(item)
        return _to_out(item)

    async def delete(self, enquiry_id: int) -> None:
        item = await self.repo.get(enquiry_id)
        if not item:
            raise NotFoundError("Enquiry not found")
        await self.repo.delete(item)
        await self.session.commit()
