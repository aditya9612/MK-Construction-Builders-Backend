from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, project_id: int) -> Project | None:
        return await self.session.get(Project, project_id)

    async def get_with_customer(self, project_id: int) -> Project | None:
        stmt = select(Project).options(selectinload(Project.customer)).where(Project.id == project_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    def list_query(
        self,
        search: str | None = None,
        customer_id: int | None = None,
        status: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select:
        stmt = select(Project)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Project.project_name.ilike(like),
                    Project.project_code.ilike(like),
                    Project.site_address.ilike(like),
                )
            )
        if customer_id is not None:
            stmt = stmt.where(Project.customer_id == customer_id)
        if status:
            stmt = stmt.where(Project.status == status)
        column = getattr(Project, sort_by, Project.created_at)
        stmt = stmt.order_by(column.asc() if sort_order == "asc" else column.desc())
        return stmt

    async def add(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project
