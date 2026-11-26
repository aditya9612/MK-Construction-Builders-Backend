"""Service layer for Instagram Reels management and public section delivery."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationFailedError
from app.models.instagram_reel import InstagramReel
from app.repositories.instagram_reel_repository import InstagramReelRepository
from app.schemas.common import PaginatedData
from app.schemas.instagram_reel import (
    InstagramReelCreate,
    InstagramReelOut,
    InstagramReelPublicListOut,
    InstagramReelPublicOut,
    InstagramReelUpdate,
    InstagramSectionSettingsOut,
    InstagramSectionSettingsUpdate,
    parse_and_normalize_instagram_url,
)
from app.utils.pagination import paginate


class InstagramReelService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = InstagramReelRepository(session)

    async def create(self, payload: InstagramReelCreate) -> InstagramReelOut:
        if payload.display_order < 0:
            raise ValidationFailedError("display_order must be non-negative")

        canonical_url, embed_url, _ = parse_and_normalize_instagram_url(payload.instagram_url)

        reel = InstagramReel(
            title=payload.title,
            instagram_url=canonical_url,
            embed_url=embed_url,
            description=payload.description,
            is_published=payload.is_published,
            display_order=payload.display_order,
        )

        try:
            await self.repo.create(reel)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram reel could not be created due to a conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while creating the Instagram reel") from exc

        await self.session.refresh(reel)
        return InstagramReelOut.model_validate(reel)

    async def get_admin(self, reel_id: int) -> InstagramReelOut:
        reel = await self.repo.get(reel_id)
        if not reel:
            raise NotFoundError("Instagram reel not found")
        return InstagramReelOut.model_validate(reel)

    async def list_admin(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_published: bool | None = None,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> PaginatedData[InstagramReelOut]:
        query = self.repo.list_query(
            search=search,
            is_published=is_published,
            published_only=False,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        items, meta = await paginate(self.session, query, page, page_size)
        return PaginatedData(
            items=[InstagramReelOut.model_validate(item) for item in items],
            total=meta.total,
            page=meta.page,
            page_size=meta.page_size,
            total_pages=meta.total_pages,
        )

    async def update(self, reel_id: int, payload: InstagramReelUpdate) -> InstagramReelOut:
        reel = await self.repo.get(reel_id)
        if not reel:
            raise NotFoundError("Instagram reel not found")

        data = payload.model_dump(exclude_unset=True)
        if not data:
            raise ValidationFailedError("At least one field must be provided for update")

        if "display_order" in data and (data["display_order"] is None or data["display_order"] < 0):
            raise ValidationFailedError("display_order must be non-negative")

        if "instagram_url" in data and data["instagram_url"] is not None:
            canonical_url, embed_url, _ = parse_and_normalize_instagram_url(data["instagram_url"])
            data["instagram_url"] = canonical_url
            data["embed_url"] = embed_url

        try:
            await self.repo.update(reel, data)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram reel update conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while updating the Instagram reel") from exc

        await self.session.refresh(reel)
        return InstagramReelOut.model_validate(reel)

    async def delete(self, reel_id: int) -> None:
        reel = await self.repo.get(reel_id)
        if not reel:
            raise NotFoundError("Instagram reel not found")

        try:
            await self.repo.delete(reel)
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram reel could not be deleted due to a conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while deleting the Instagram reel") from exc

    async def set_publish_status(self, reel_id: int, is_published: bool) -> InstagramReelOut:
        reel = await self.repo.get(reel_id)
        if not reel:
            raise NotFoundError("Instagram reel not found")

        try:
            await self.repo.update(reel, {"is_published": is_published})
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram reel publish update conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while updating publish status") from exc

        await self.session.refresh(reel)
        return InstagramReelOut.model_validate(reel)

    async def set_display_order(self, reel_id: int, display_order: int) -> InstagramReelOut:
        if display_order < 0:
            raise ValidationFailedError("display_order must be non-negative")

        reel = await self.repo.get(reel_id)
        if not reel:
            raise NotFoundError("Instagram reel not found")

        try:
            await self.repo.update(reel, {"display_order": display_order})
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram reel display order update conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while updating display order") from exc

        await self.session.refresh(reel)
        return InstagramReelOut.model_validate(reel)

    async def get_settings(self) -> InstagramSectionSettingsOut:
        try:
            settings, created = await self.repo.get_or_create_settings()
            if created:
                await self.session.commit()
                await self.session.refresh(settings)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram section settings conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while loading settings") from exc

        return InstagramSectionSettingsOut.model_validate(settings)

    async def update_settings(
        self, payload: InstagramSectionSettingsUpdate
    ) -> InstagramSectionSettingsOut:
        try:
            settings, _ = await self.repo.get_or_create_settings()
            settings.is_enabled = payload.is_enabled
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram section settings update conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while updating settings") from exc

        await self.session.refresh(settings)
        return InstagramSectionSettingsOut.model_validate(settings)

    async def list_public(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> InstagramReelPublicListOut:
        safe_page = max(page, 1)
        safe_page_size = min(max(page_size, 1), 100)

        try:
            settings, created = await self.repo.get_or_create_settings()
            if created:
                await self.session.commit()
                await self.session.refresh(settings)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Instagram section settings conflict") from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise DatabaseError("A database error occurred while loading settings") from exc

        if not settings.is_enabled:
            return InstagramReelPublicListOut(
                is_enabled=False,
                items=[],
                total=0,
                page=safe_page,
                page_size=safe_page_size,
                total_pages=0,
            )

        query = self.repo.list_query(
            published_only=True,
            sort_by="display_order",
            sort_order="asc",
        )
        items, meta = await paginate(self.session, query, safe_page, safe_page_size)
        return InstagramReelPublicListOut(
            is_enabled=True,
            items=[InstagramReelPublicOut.model_validate(item) for item in items],
            total=meta.total,
            page=meta.page,
            page_size=meta.page_size,
            total_pages=meta.total_pages,
        )
