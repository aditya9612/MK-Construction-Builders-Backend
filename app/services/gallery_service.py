"""Website gallery service."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.core.media_settings import get_media_settings
from app.models.gallery_item import GalleryItem
from app.repositories.gallery_repository import GalleryRepository
from app.repositories.media_repository import MediaRepository
from app.schemas.common import PaginatedData
from app.schemas.gallery import GalleryItemCreate, GalleryItemOut, GalleryItemUpdate, gallery_item_to_out
from app.utils.pagination import paginate


class GalleryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GalleryRepository(session)
        self.media_repo = MediaRepository(session)
        self.media_settings = get_media_settings()

    async def _ensure_media(self, media_id: int):
        media = await self.media_repo.get(media_id)
        if not media:
            raise ValidationFailedError(f"Media id {media_id} not found")
        return media

    def _to_out(self, item: GalleryItem) -> GalleryItemOut:
        return gallery_item_to_out(
            item,
            public_base_url=self.media_settings.public_base_url,
        )

    async def create(self, payload: GalleryItemCreate) -> GalleryItemOut:
        await self._ensure_media(payload.media_id)
        item = GalleryItem(
            media_id=payload.media_id,
            caption=payload.caption,
            category=payload.category.value,
            object_position=payload.object_position,
            display_order=payload.display_order,
            publication_status=payload.publication_status.value,
            notes=payload.notes,
        )
        try:
            await self.repo.add(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Gallery item could not be created") from exc

        loaded = await self.repo.get_with_media(item.id)
        assert loaded is not None
        return self._to_out(loaded)

    async def get_admin(self, item_id: int) -> GalleryItemOut:
        item = await self.repo.get_with_media(item_id)
        if not item:
            raise NotFoundError("Gallery item not found")
        return self._to_out(item)

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        category: object | None = None,
        search: str | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[GalleryItemOut]:
        cat_val = category.value if hasattr(category, "value") else category
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                category=cat_val,
                search=search,
                published_only=True,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            page,
            page_size,
        )
        return PaginatedData(
            items=[self._to_out(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def list_admin(
        self,
        *,
        page: int,
        page_size: int,
        category: object | None = None,
        search: str | None = None,
        publication_status: object | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[GalleryItemOut]:
        cat_val = category.value if hasattr(category, "value") else category
        pub_val = (
            publication_status.value
            if hasattr(publication_status, "value")
            else publication_status
        )
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                category=cat_val,
                search=search,
                publication_status=pub_val,
                published_only=False,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            page,
            page_size,
        )
        return PaginatedData(
            items=[self._to_out(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )


    async def update(self, item_id: int, payload: GalleryItemUpdate) -> GalleryItemOut:
        item = await self.repo.get(item_id)
        if not item:
            raise NotFoundError("Gallery item not found")

        data = payload.model_dump(exclude_unset=True)
        if "media_id" in data and data["media_id"] is not None:
            await self._ensure_media(data["media_id"])

        for key, value in data.items():
            if key in {"category", "publication_status"} and value is not None:
                setattr(item, key, value.value if hasattr(value, "value") else value)
            else:
                setattr(item, key, value)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Gallery item update conflict") from exc

        loaded = await self.repo.get_with_media(item_id)
        assert loaded is not None
        return self._to_out(loaded)

    async def delete(self, item_id: int) -> None:
        item = await self.repo.get(item_id)
        if not item:
            raise NotFoundError("Gallery item not found")
        await self.repo.delete(item)
        await self.session.commit()
