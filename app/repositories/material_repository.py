from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.masters import MaterialMaster


class MaterialRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, material_id: int) -> MaterialMaster | None:
        return await self.session.get(MaterialMaster, material_id)

    def list_query(
        self,
        search: str | None = None,
        category: str | None = None,
        brand: str | None = None,
        is_active: bool | None = None,
    ) -> Select:
        stmt = select(MaterialMaster)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    MaterialMaster.name.ilike(like),
                    MaterialMaster.brand.ilike(like),
                    MaterialMaster.specification.ilike(like),
                )
            )
        if category:
            stmt = stmt.where(MaterialMaster.category == category)
        if brand:
            stmt = stmt.where(MaterialMaster.brand.ilike(like))
        if is_active is not None:
            stmt = stmt.where(MaterialMaster.is_active.is_(is_active))
        return stmt.order_by(MaterialMaster.name.asc())

    async def add(self, material: MaterialMaster) -> MaterialMaster:
        self.session.add(material)
        await self.session.flush()
        return material
