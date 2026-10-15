"""Repository for website gallery items."""

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cms_enums import PublicationStatus
from app.models.gallery_item import GalleryItem


ALLOWED_GALLERY_SORT_FIELDS = frozenset(
    {"display_order", "created_at", "updated_at", "category", "id"}
)


class GalleryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, item_id: int) -> GalleryItem | None:
        return await self.session.get(GalleryItem, item_id)

    async def get_with_media(self, item_id: int) -> GalleryItem | None:
        stmt = (
            select(GalleryItem)
            .options(selectinload(GalleryItem.media))
            .where(GalleryItem.id == item_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def list_query(
        self,
        *,
        category: str | None = None,
        search: str | None = None,
        publication_status: str | None = None,
        published_only: bool = False,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> Select:
        stmt = select(GalleryItem).options(selectinload(GalleryItem.media))
        if published_only:
            stmt = stmt.where(
                GalleryItem.publication_status == PublicationStatus.PUBLISHED.value
            )
        elif publication_status:
            stmt = stmt.where(GalleryItem.publication_status == publication_status)
        if category:
            stmt = stmt.where(GalleryItem.category == category)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    GalleryItem.caption.ilike(like),
                    GalleryItem.notes.ilike(like),
                )
            )

        safe_sort_by = sort_by if sort_by in ALLOWED_GALLERY_SORT_FIELDS else "display_order"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"

        if safe_sort_by == "display_order":
            primary = GalleryItem.display_order
            secondary = GalleryItem.created_at.desc()
            stmt = stmt.order_by(
                primary.asc() if safe_sort_order == "asc" else primary.desc(),
                secondary,
            )
        else:
            column = getattr(GalleryItem, safe_sort_by, GalleryItem.created_at)
            stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())
        return stmt


    async def add(self, item: GalleryItem) -> GalleryItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def delete(self, item: GalleryItem) -> None:
        await self.session.delete(item)
