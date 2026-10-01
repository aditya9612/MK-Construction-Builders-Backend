from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.masters import MaterialMaster
from app.models.user import User
from app.repositories.material_repository import MaterialRepository
from app.schemas.common import PaginatedData
from app.schemas.material import MaterialCreate, MaterialOut, MaterialUpdate
from app.services.audit_service import AuditService
from app.utils.pagination import paginate


class MaterialService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = MaterialRepository(session)
        self.audit = AuditService(session)

    async def create(self, payload: MaterialCreate, user: User) -> MaterialOut:
        material = MaterialMaster(**payload.model_dump())
        await self.repo.add(material)
        await self.audit.log(
            user_id=user.id,
            action="material.created",
            entity_type="material_master",
            entity_id=material.id,
            new_data={"name": material.name},
        )
        await self.session.commit()
        await self.session.refresh(material)
        return MaterialOut.model_validate(material)

    async def get(self, material_id: int) -> MaterialOut:
        material = await self.repo.get(material_id)
        if not material:
            raise NotFoundError("Material not found")
        return MaterialOut.model_validate(material)

    async def list(self, *, page: int, page_size: int, **filters) -> PaginatedData[MaterialOut]:
        items, data = await paginate(self.session, self.repo.list_query(**filters), page, page_size)
        return PaginatedData(
            items=[MaterialOut.model_validate(i) for i in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, material_id: int, payload: MaterialUpdate, user: User) -> MaterialOut:
        material = await self.repo.get(material_id)
        if not material:
            raise NotFoundError("Material not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(material, key, value)
        await self.audit.log(
            user_id=user.id,
            action="material.changed",
            entity_type="material_master",
            entity_id=material.id,
            new_data={"name": material.name},
        )
        await self.session.commit()
        await self.session.refresh(material)
        return MaterialOut.model_validate(material)

    async def delete(self, material_id: int) -> None:
        material = await self.repo.get(material_id)
        if not material:
            raise NotFoundError("Material not found")
        material.is_active = False
        await self.session.commit()
