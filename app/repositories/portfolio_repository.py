"""Repository for website portfolio projects (not ERP projects)."""

from sqlalchemy import Select, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cms_enums import PublicationStatus
from app.models.portfolio_gallery import PortfolioProjectGallery
from app.models.portfolio_project import PortfolioProject


ALLOWED_PORTFOLIO_SORT_FIELDS = frozenset(
    {"display_order", "created_at", "updated_at", "name", "slug", "status", "type", "id"}
)


class PortfolioRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, project_id: int) -> PortfolioProject | None:
        return await self.session.get(PortfolioProject, project_id)

    async def get_with_relations(self, project_id: int) -> PortfolioProject | None:
        stmt = (
            select(PortfolioProject)
            .options(
                selectinload(PortfolioProject.main_image),
                selectinload(PortfolioProject.gallery_links).selectinload(
                    PortfolioProjectGallery.media
                ),
            )
            .where(PortfolioProject.id == project_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_slug(
        self,
        slug: str,
        *,
        published_only: bool = False,
    ) -> PortfolioProject | None:
        stmt = (
            select(PortfolioProject)
            .options(
                selectinload(PortfolioProject.main_image),
                selectinload(PortfolioProject.gallery_links).selectinload(
                    PortfolioProjectGallery.media
                ),
            )
            .where(PortfolioProject.slug == slug)
        )
        if published_only:
            stmt = stmt.where(
                PortfolioProject.publication_status == PublicationStatus.PUBLISHED.value
            )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def slug_exists(self, slug: str, *, exclude_id: int | None = None) -> bool:
        stmt = select(PortfolioProject.id).where(PortfolioProject.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(PortfolioProject.id != exclude_id)
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    def list_query(
        self,
        *,
        search: str | None = None,
        project_type: str | None = None,
        status: str | None = None,
        publication_status: str | None = None,
        published_only: bool = False,
        sort_by: str = "display_order",
        sort_order: str = "asc",
    ) -> Select:
        stmt = select(PortfolioProject).options(selectinload(PortfolioProject.main_image))
        if published_only:
            stmt = stmt.where(
                PortfolioProject.publication_status == PublicationStatus.PUBLISHED.value
            )
        elif publication_status:
            stmt = stmt.where(PortfolioProject.publication_status == publication_status)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    PortfolioProject.name.ilike(like),
                    PortfolioProject.slug.ilike(like),
                    PortfolioProject.location.ilike(like),
                )
            )
        if project_type:
            stmt = stmt.where(PortfolioProject.type == project_type)
        if status:
            stmt = stmt.where(PortfolioProject.status == status)

        safe_sort_by = sort_by if sort_by in ALLOWED_PORTFOLIO_SORT_FIELDS else "display_order"
        safe_sort_order = "asc" if str(sort_order).lower() == "asc" else "desc"

        if safe_sort_by == "display_order":
            primary = PortfolioProject.display_order
            secondary = PortfolioProject.created_at.desc()
            stmt = stmt.order_by(
                primary.asc() if safe_sort_order == "asc" else primary.desc(),
                secondary,
            )
        else:
            column = getattr(PortfolioProject, safe_sort_by, PortfolioProject.created_at)
            stmt = stmt.order_by(column.asc() if safe_sort_order == "asc" else column.desc())
        return stmt


    async def add(self, project: PortfolioProject) -> PortfolioProject:
        self.session.add(project)
        await self.session.flush()
        return project

    async def delete(self, project: PortfolioProject) -> None:
        await self.session.delete(project)

    async def add_gallery_link(self, link: PortfolioProjectGallery) -> PortfolioProjectGallery:
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_gallery_link(
        self, project_id: int, media_id: int
    ) -> PortfolioProjectGallery | None:
        stmt = select(PortfolioProjectGallery).where(
            PortfolioProjectGallery.portfolio_project_id == project_id,
            PortfolioProjectGallery.media_id == media_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def delete_gallery_links(self, project_id: int, media_ids: list[int]) -> int:
        if not media_ids:
            return 0
        stmt = delete(PortfolioProjectGallery).where(
            PortfolioProjectGallery.portfolio_project_id == project_id,
            PortfolioProjectGallery.media_id.in_(media_ids),
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    async def max_gallery_order(self, project_id: int) -> int:
        from sqlalchemy import func

        stmt = select(func.coalesce(func.max(PortfolioProjectGallery.display_order), -1)).where(
            PortfolioProjectGallery.portfolio_project_id == project_id
        )
        return int((await self.session.execute(stmt)).scalar_one())
