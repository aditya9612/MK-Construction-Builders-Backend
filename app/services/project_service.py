from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.models.project import Project
from app.repositories.customer_repository import CustomerRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PaginatedData
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.utils.pagination import paginate
from app.utils.quotation_number import generate_coded_number


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ProjectRepository(session)
        self.customers = CustomerRepository(session)

    async def _ensure_customer(self, customer_id: int):
        customer = await self.customers.get(customer_id)
        if not customer or not customer.is_active:
            raise ValidationFailedError("Customer not found or inactive")
        return customer

    async def create(self, payload: ProjectCreate) -> ProjectOut:
        await self._ensure_customer(payload.customer_id)
        code = await generate_coded_number(self.session, Project, "project_code", "MKP")
        project = Project(project_code=code, **payload.model_dump())
        await self.repo.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return ProjectOut.model_validate(project)

    async def get(self, project_id: int) -> ProjectOut:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Project not found")
        return ProjectOut.model_validate(project)

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        customer_id: int | None,
        status: str | None,
        sort_by: str,
        sort_order: str,
    ) -> PaginatedData[ProjectOut]:
        items, data = await paginate(
            self.session,
            self.repo.list_query(search, customer_id, status, sort_by, sort_order),
            page,
            page_size,
        )
        return PaginatedData(
            items=[ProjectOut.model_validate(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, project_id: int, payload: ProjectUpdate) -> ProjectOut:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Project not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        await self.session.commit()
        await self.session.refresh(project)
        return ProjectOut.model_validate(project)

    async def delete(self, project_id: int) -> None:
        project = await self.repo.get(project_id)
        if not project:
            raise NotFoundError("Project not found")
        await self.session.delete(project)
        await self.session.commit()
