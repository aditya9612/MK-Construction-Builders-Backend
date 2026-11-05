"""Repository for website CMS services."""

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cms_enums import PublicationStatus
from app.models.website_service import WebsiteService


ALLOWED_SERVICE_SORT_FIELDS = frozenset(
    {"display_order", "created_at", "updated_at", "title", "slug", "id"}
)


class WebsiteServiceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, service_id: int) -> WebsiteService | None:
        return await self.session.get(WebsiteService, service_id)

    async def get_with_image(self, service_id: int) -> WebsiteService | None:
        stmt = (
            select(WebsiteService)
            .options(selectinload(WebsiteService.image))
            .where(WebsiteService.id == service_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_slug(
        self,
        slug: str,
        *,
        published_only: bool = False,
    ) -> WebsiteService | None:
        stmt = (
            select(WebsiteService)
            .options(selectinload(WebsiteService.image))
            .where(WebsiteService.slug == slug)
        )
        if published_only:
            stmt = stmt.where(
                WebsiteService.publication_status == PublicationStatus.PUBLISHED.value
            )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def slug_exists(self, slug: str, *, exclude_id: int | None = None) -> bool:
        stmt = select(WebsiteService.id).where(WebsiteService.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(WebsiteService.id != exclude_id)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    def list_query(
        self,
        *,
        search: str | None = None,
        publication_status: str | None = None,
        published_only: bool = False,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> Select:
        stmt = select(WebsiteService).options(selectinload(WebsiteService.image))
        if published_only:
            stmt = stmt.where(
                WebsiteService.publication_status == PublicationStatus.PUBLISHED.value
            )
        elif publication_status:
            stmt = stmt.where(WebsiteService.publication_status == publication_status)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    WebsiteService.title.ilike(like),
                    WebsiteService.slug.ilike(like),
                    WebsiteService.description.ilike(like),
                )
            )

        safe_sort_by = sort_by if sort_by in ALLOWED_SERVICE_SORT_FIELDS else "display_order"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"

        if safe_sort_by == "display_order":
            primary = WebsiteService.display_order
            secondary = WebsiteService.created_at.desc()
            stmt = stmt.order_by(
                primary.asc() if safe_sort_order == "asc" else primary.desc(),
                secondary,
            )
        else:
            column = getattr(WebsiteService, safe_sort_by, WebsiteService.created_at)
            stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())
        return stmt

    async def add(self, item: WebsiteService) -> WebsiteService:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, item: WebsiteService) -> None:
        await self.session.delete(item)
