"""Website portfolio service — separate from ERP ProjectService."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.core.media_settings import get_media_settings
from app.models.portfolio_gallery import PortfolioProjectGallery
from app.models.portfolio_project import PortfolioProject
from app.models.uploaded_media import UploadedMedia
from app.repositories.media_repository import MediaRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.common import PaginatedData
from app.schemas.portfolio import (
    PortfolioGalleryAttach,
    PortfolioGalleryDetach,
    PortfolioGalleryImageOut,
    PortfolioProjectCreate,
    PortfolioProjectListItemOut,
    PortfolioProjectOut,
    PortfolioProjectUpdate,
)
from app.schemas.uploaded_media import MediaRefOut
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


def _to_out(project: PortfolioProject) -> PortfolioProjectOut:
    gallery = [
        PortfolioGalleryImageOut(
            id=link.id,
            media_id=link.media_id,
            display_order=link.display_order,
            media=_media_ref(link.media),
        )
        for link in sorted(
            project.gallery_links, key=lambda item: (item.display_order, item.id or 0)
        )
    ]

    return PortfolioProjectOut(
        id=project.id,
        name=project.name,
        slug=project.slug,
        location=project.location,
        type=project.type,
        status=project.status,
        main_image_id=project.main_image_id,
        main_image=_media_ref(project.main_image),
        description=project.description,
        overview=project.overview,
        work_progress=project.work_progress,
        final_result=project.final_result,
        publication_status=project.publication_status,
        display_order=project.display_order,
        gallery=gallery,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _to_list_item(project: PortfolioProject) -> PortfolioProjectListItemOut:
    return PortfolioProjectListItemOut(
        id=project.id,
        name=project.name,
        slug=project.slug,
        location=project.location,
        type=project.type,
        status=project.status,
        main_image=_media_ref(project.main_image),
        publication_status=project.publication_status,
        display_order=project.display_order,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


class PortfolioService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PortfolioRepository(session)
        self.media_repo = MediaRepository(session)
        self.media_settings = get_media_settings()

    async def _ensure_media(self, media_id: int) -> UploadedMedia:
        media = await self.media_repo.get(media_id)
        if not media:
            raise ValidationFailedError(f"Media id {media_id} not found")
        return media

    async def create(self, payload: PortfolioProjectCreate) -> PortfolioProjectOut:
        if await self.repo.slug_exists(payload.slug):
            raise ConflictError("Portfolio project slug already exists")

        if payload.main_image_id is not None:
            await self._ensure_media(payload.main_image_id)
        if payload.gallery_media_ids:
            found = await self.media_repo.get_many(payload.gallery_media_ids)
            if len(found) != len(payload.gallery_media_ids):
                raise ValidationFailedError("One or more gallery media ids were not found")

        project = PortfolioProject(
            name=payload.name,
            slug=payload.slug,
            location=payload.location,
            type=payload.type.value,
            status=payload.status.value,
            main_image_id=payload.main_image_id,
            description=payload.description,
            overview=payload.overview,
            work_progress=payload.work_progress,
            final_result=payload.final_result,
            publication_status=payload.publication_status.value,
            display_order=payload.display_order,
        )
        try:
            await self.repo.add(project)
            for index, media_id in enumerate(payload.gallery_media_ids):
                await self.repo.add_gallery_link(
                    PortfolioProjectGallery(
                        portfolio_project_id=project.id,
                        media_id=media_id,
                        display_order=index,
                    )
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Portfolio project could not be created due to a conflict") from exc

        loaded = await self.repo.get_with_relations(project.id)
        assert loaded is not None
        return _to_out(loaded)

    async def get_public_by_slug(self, slug: str) -> PortfolioProjectOut:
        project = await self.repo.get_by_slug(slug, published_only=True)
        if not project:
            raise NotFoundError("Portfolio project not found")
        return _to_out(project)

    async def get_admin(self, project_id: int) -> PortfolioProjectOut:
        project = await self.repo.get_with_relations(project_id)
        if not project:
            raise NotFoundError("Portfolio project not found")
        return _to_out(project)

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        project_type: object | None = None,
        status: object | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[PortfolioProjectListItemOut]:
        type_val = project_type.value if hasattr(project_type, "value") else project_type
        status_val = status.value if hasattr(status, "value") else status
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                search=search,
                project_type=type_val,
                status=status_val,
                published_only=True,
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

    async def list_admin(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        project_type: object | None = None,
        status: object | None = None,
        publication_status: object | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[PortfolioProjectListItemOut]:
        type_val = project_type.value if hasattr(project_type, "value") else project_type
        status_val = status.value if hasattr(status, "value") else status
        pub_val = (
            publication_status.value
            if hasattr(publication_status, "value")
            else publication_status
        )
        items, data = await paginate(
            self.session,
            self.repo.list_query(
                search=search,
                project_type=type_val,
                status=status_val,
                publication_status=pub_val,
                published_only=False,
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


    async def update(self, project_id: int, payload: PortfolioProjectUpdate) -> PortfolioProjectOut:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Portfolio project not found")

        data = payload.model_dump(exclude_unset=True)
        clear_main = data.pop("clear_main_image", False)

        if "slug" in data and data["slug"] != project.slug:
            if await self.repo.slug_exists(data["slug"], exclude_id=project_id):
                raise ConflictError("Portfolio project slug already exists")

        if data.get("main_image_id") is not None:
            await self._ensure_media(data["main_image_id"])

        for key, value in data.items():
            if key in {"type", "status", "publication_status"} and value is not None:
                setattr(project, key, value.value if hasattr(value, "value") else value)
            else:
                setattr(project, key, value)

        if clear_main:
            project.main_image_id = None

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Portfolio project update conflict") from exc

        loaded = await self.repo.get_with_relations(project_id)
        assert loaded is not None
        return _to_out(loaded)

    async def delete(self, project_id: int) -> None:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Portfolio project not found")
        await self.repo.delete(project)
        await self.session.commit()

    async def attach_gallery(
        self, project_id: int, payload: PortfolioGalleryAttach
    ) -> PortfolioProjectOut:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Portfolio project not found")

        found = await self.media_repo.get_many(payload.media_ids)
        if len(found) != len(payload.media_ids):
            raise ValidationFailedError("One or more media ids were not found")

        next_order = await self.repo.max_gallery_order(project_id) + 1
        try:
            for index, media_id in enumerate(payload.media_ids):
                existing = await self.repo.get_gallery_link(project_id, media_id)
                if existing:
                    if payload.display_orders is not None:
                        existing.display_order = payload.display_orders[index]
                    continue
                order = (
                    payload.display_orders[index]
                    if payload.display_orders is not None
                    else next_order + index
                )
                await self.repo.add_gallery_link(
                    PortfolioProjectGallery(
                        portfolio_project_id=project_id,
                        media_id=media_id,
                        display_order=order,
                    )
                )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Gallery attachment conflict") from exc

        loaded = await self.repo.get_with_relations(project_id)
        assert loaded is not None
        return _to_out(loaded)

    async def detach_gallery(
        self, project_id: int, payload: PortfolioGalleryDetach
    ) -> PortfolioProjectOut:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Portfolio project not found")

        removed = await self.repo.delete_gallery_links(project_id, payload.media_ids)
        if removed == 0:
            raise NotFoundError("No matching gallery media links found for this project")
        await self.session.commit()

        loaded = await self.repo.get_with_relations(project_id)
        assert loaded is not None
        return _to_out(loaded)

    async def detach_gallery_media(
        self, project_id: int, media_id: int
    ) -> PortfolioProjectOut:
        return await self.detach_gallery(
            project_id, PortfolioGalleryDetach(media_ids=[media_id])
        )

