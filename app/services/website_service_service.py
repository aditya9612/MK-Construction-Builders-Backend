"""Website CMS services — separate from ERP modules."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.models.uploaded_media import UploadedMedia
from app.models.website_service import WebsiteService
from app.repositories.media_repository import MediaRepository
from app.repositories.website_service_repository import WebsiteServiceRepository
from app.schemas.common import PaginatedData
from app.schemas.uploaded_media import MediaRefOut
from app.schemas.website_service import (
    WebsiteServiceCreate,
    WebsiteServiceOut,
    WebsiteServiceUpdate,
)
from app.utils.pagination import paginate


def _media_ref(media: UploadedMedia | None) -> MediaRefOut | None:
    if media is None:
        return None
    return MediaRefOut(
        id=media.id,
        url_path=media.url_path,
        mime_type=media.mime_type,
        width=media.width,
        height=media.height,
        original_filename=media.original_filename,
    )


def _to_out(item: WebsiteService) -> WebsiteServiceOut:
    features = item.features if isinstance(item.features, list) else []
    return WebsiteServiceOut(
        id=item.id,
        title=item.title,
        slug=item.slug,
        description=item.description,
        features=[str(feature) for feature in features],
        image_id=item.image_id,
        image=_media_ref(item.image),
        publication_status=item.publication_status,
        display_order=item.display_order,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


class WebsiteServiceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WebsiteServiceRepository(session)
        self.media_repo = MediaRepository(session)

    async def _ensure_media(self, media_id: int) -> UploadedMedia:
        media = await self.media_repo.get(media_id)
        if not media:
            raise ValidationFailedError(f"Media id {media_id} not found")
        return media

    async def create(self, payload: WebsiteServiceCreate) -> WebsiteServiceOut:
        if await self.repo.slug_exists(payload.slug):
            raise ConflictError("Service slug already exists")
        await self._ensure_media(payload.image_id)

        item = WebsiteService(
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
            features=payload.features,
            image_id=payload.image_id,
            display_order=payload.display_order,
            publication_status=payload.publication_status.value,
        )
        try:
            await self.repo.add(item)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Service could not be created due to a conflict") from exc

        loaded = await self.repo.get_with_image(item.id)
        assert loaded is not None
        return _to_out(loaded)

    async def get_public_by_slug(self, slug: str) -> WebsiteServiceOut:
        item = await self.repo.get_by_slug(slug, published_only=True)
        if not item:
            raise NotFoundError("Service not found")
        return _to_out(item)

    async def get_admin(self, service_id: int) -> WebsiteServiceOut:
        item = await self.repo.get_with_image(service_id)
        if not item:
            raise NotFoundError("Service not found")
        return _to_out(item)

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[WebsiteServiceOut]:
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                search=search,
                published_only=True,
                sort_by=sort_by,
                sort_order=sort_order,
            ),
            page,
            page_size,
        )
        return PaginatedData(
            items=[_to_out(item) for item in items],
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
        search: str | None = None,
        publication_status: object | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[WebsiteServiceOut]:
        pub_val = (
            publication_status.value
            if hasattr(publication_status, "value")
            else publication_status
        )
        items, data = await paginate(
            self.session,
            self.repo.list_query(
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
            items=[_to_out(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, service_id: int, payload: WebsiteServiceUpdate) -> WebsiteServiceOut:
        item = await self.repo.get(service_id)
        if not item:
            raise NotFoundError("Service not found")

        data = payload.model_dump(exclude_unset=True)
        if "slug" in data and data["slug"] != item.slug:
            if await self.repo.slug_exists(data["slug"], exclude_id=service_id):
                raise ConflictError("Service slug already exists")

        if data.get("image_id") is not None:
            await self._ensure_media(data["image_id"])

        for key, value in data.items():
            if key == "publication_status" and value is not None:
                setattr(item, key, value.value if hasattr(value, "value") else value)
            else:
                setattr(item, key, value)

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Service update conflict") from exc

        loaded = await self.repo.get_with_image(service_id)
        assert loaded is not None
        return _to_out(loaded)

    async def delete(self, service_id: int) -> None:
        item = await self.repo.get(service_id)
        if not item:
            raise NotFoundError("Service not found")
        await self.repo.delete(item)
        await self.session.commit()
