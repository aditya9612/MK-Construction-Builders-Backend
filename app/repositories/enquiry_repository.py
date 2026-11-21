"""Repository for website enquiries."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cms_enums import EnquiryStatus
from app.models.enquiry import WebsiteEnquiry

ALLOWED_ENQUIRY_SORT_FIELDS = frozenset(
    {"created_at", "updated_at", "name", "mobile", "status", "id", "is_read"}
)

RATE_LIMIT_WINDOW = timedelta(minutes=10)
RATE_LIMIT_MAX = 3


class EnquiryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, enquiry_id: int) -> WebsiteEnquiry | None:
        return await self.session.get(WebsiteEnquiry, enquiry_id)

    async def recent_count_for_mobile(self, mobile: str, *, since: datetime) -> int:
        stmt = select(func.count(WebsiteEnquiry.id)).where(
            WebsiteEnquiry.mobile == mobile,
            WebsiteEnquiry.created_at >= since,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def unread_count(self) -> int:
        stmt = select(func.count(WebsiteEnquiry.id)).where(
            WebsiteEnquiry.is_read.is_(False),
            WebsiteEnquiry.status != EnquiryStatus.SPAM.value,
        )
        return int((await self.session.execute(stmt)).scalar_one())

    def list_query(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        is_read: bool | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select:
        stmt = select(WebsiteEnquiry)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    WebsiteEnquiry.name.ilike(like),
                    WebsiteEnquiry.mobile.ilike(like),
                    WebsiteEnquiry.email.ilike(like),
                    WebsiteEnquiry.location.ilike(like),
                )
            )
        if status:
            stmt = stmt.where(WebsiteEnquiry.status == status)
        if is_read is not None:
            stmt = stmt.where(WebsiteEnquiry.is_read.is_(is_read))
        if date_from:
            start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            stmt = stmt.where(WebsiteEnquiry.created_at >= start)
        if date_to:
            end = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            stmt = stmt.where(WebsiteEnquiry.created_at <= end)

        safe_sort_by = sort_by if sort_by in ALLOWED_ENQUIRY_SORT_FIELDS else "created_at"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"
        column = getattr(WebsiteEnquiry, safe_sort_by, WebsiteEnquiry.created_at)
        stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())
        return stmt

    async def add(self, item: WebsiteEnquiry) -> WebsiteEnquiry:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, item: WebsiteEnquiry) -> None:
        await self.session.delete(item)
