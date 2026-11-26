"""Repository for Instagram Reels and singleton section settings."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instagram_reel import InstagramReel, InstagramSectionSettings

ALLOWED_REEL_SORT_FIELDS = frozenset(
    {"display_order", "created_at", "updated_at", "title", "id", "is_published"}
)


class InstagramReelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, reel: InstagramReel) -> InstagramReel:
        self.session.add(reel)
        await self.session.flush()
        return reel

    async def get(self, reel_id: int) -> InstagramReel | None:
        return await self.session.get(InstagramReel, reel_id)

    async def update(self, reel: InstagramReel, data: dict[str, Any]) -> InstagramReel:
        for key, value in data.items():
            setattr(reel, key, value)
        await self.session.flush()
        return reel

    async def delete(self, reel: InstagramReel) -> None:
        await self.session.delete(reel)
        await self.session.flush()

    def list_query(
        self,
        *,
        search: str | None = None,
        is_published: bool | None = None,
        published_only: bool = False,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> Select:
        stmt = select(InstagramReel)

        if published_only:
            stmt = stmt.where(InstagramReel.is_published.is_(True))
        elif is_published is not None:
            stmt = stmt.where(InstagramReel.is_published.is_(is_published))

        if search and search.strip():
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    InstagramReel.title.ilike(like),
                    InstagramReel.description.ilike(like),
                    InstagramReel.instagram_url.ilike(like),
                )
            )

        safe_sort_by = sort_by if sort_by in ALLOWED_REEL_SORT_FIELDS else "display_order"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"

        if safe_sort_by == "display_order":
            primary = InstagramReel.display_order
            stmt = stmt.order_by(
                primary.asc() if safe_sort_order == "asc" else primary.desc(),
                InstagramReel.created_at.desc(),
                InstagramReel.id.desc(),
            )
        else:
            column = getattr(InstagramReel, safe_sort_by, InstagramReel.created_at)
            stmt = stmt.order_by(
                column.asc() if safe_sort_order == "asc" else column.desc(),
                InstagramReel.id.asc() if safe_sort_order == "asc" else InstagramReel.id.desc(),
            )

        return stmt

    async def get_settings(self, *, for_update: bool = False) -> InstagramSectionSettings | None:
        stmt = (
            select(InstagramSectionSettings)
            .where(InstagramSectionSettings.id == 1)
            .execution_options(populate_existing=True)
        )
        if for_update:
            stmt = stmt.with_for_update()
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_or_create_settings(self) -> tuple[InstagramSectionSettings, bool]:
        """Return the singleton settings row, initializing it safely under concurrency.

        Returns:
            (settings_row, created_now)
        """
        existing = await self.get_settings()
        if existing is not None:
            return existing, False

        settings = InstagramSectionSettings(id=1, is_enabled=True)
        try:
            async with self.session.begin_nested():
                self.session.add(settings)
                await self.session.flush()
            return settings, True
        except IntegrityError:
            # Another concurrent transaction inserted id=1 first; locking read
            # bypasses REPEATABLE READ snapshot visibility in MySQL InnoDB.
            existing = await self.get_settings(for_update=True)
            if existing is not None:
                return existing, False
            raise
