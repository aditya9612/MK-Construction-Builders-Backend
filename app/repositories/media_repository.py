"""Repository for website CMS uploaded media."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gallery_item import GalleryItem
from app.models.portfolio_gallery import PortfolioProjectGallery
from app.models.portfolio_project import PortfolioProject
from app.models.uploaded_media import UploadedMedia


ALLOWED_MEDIA_SORT_FIELDS = frozenset(
    {"created_at", "updated_at", "original_filename", "stored_filename", "folder", "size_bytes", "id"}
)


class MediaRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, media_id: int) -> UploadedMedia | None:
        return await self.session.get(UploadedMedia, media_id)

    async def get_many(self, media_ids: list[int]) -> list[UploadedMedia]:
        if not media_ids:
            return []
        stmt = select(UploadedMedia).where(UploadedMedia.id.in_(media_ids))
        return list((await self.session.execute(stmt)).scalars().all())

    async def add(self, media: UploadedMedia) -> UploadedMedia:
        self.session.add(media)
        await self.session.flush()
        return media

    async def delete(self, media: UploadedMedia) -> None:
        await self.session.delete(media)

    async def count_references(self, media_id: int) -> int:
        """Count portfolio/gallery references that block media deletion."""
        main_count = (
            await self.session.execute(
                select(func.count())
                .select_from(PortfolioProject)
                .where(PortfolioProject.main_image_id == media_id)
            )
        ).scalar_one()
        gallery_link_count = (
            await self.session.execute(
                select(func.count())
                .select_from(PortfolioProjectGallery)
                .where(PortfolioProjectGallery.media_id == media_id)
            )
        ).scalar_one()
        gallery_item_count = (
            await self.session.execute(
                select(func.count())
                .select_from(GalleryItem)
                .where(GalleryItem.media_id == media_id)
            )
        ).scalar_one()
        return int(main_count) + int(gallery_link_count) + int(gallery_item_count)

    def list_query(
        self,
        *,
        folder: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select:
        stmt = select(UploadedMedia)
        if folder:
            stmt = stmt.where(UploadedMedia.folder == folder)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    UploadedMedia.original_filename.ilike(like),
                    UploadedMedia.stored_filename.ilike(like),
                )
            )
        safe_sort_by = sort_by if sort_by in ALLOWED_MEDIA_SORT_FIELDS else "created_at"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"
        column = getattr(UploadedMedia, safe_sort_by, UploadedMedia.created_at)
        stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())
        return stmt

