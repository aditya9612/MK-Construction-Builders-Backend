from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.masters import RateMaster


class RateRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, rate_id: int) -> RateMaster | None:
        return await self.session.get(RateMaster, rate_id)

    def list_query(
        self,
        search: str | None = None,
        category: str | None = None,
        unit: str | None = None,
        is_active: bool | None = None,
    ) -> Select:
        stmt = select(RateMaster)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(RateMaster.name.ilike(like), RateMaster.description.ilike(like)))
        if category:
            stmt = stmt.where(RateMaster.category == category)
        if unit:
            stmt = stmt.where(RateMaster.unit == unit)
        if is_active is not None:
            stmt = stmt.where(RateMaster.is_active.is_(is_active))
        return stmt.order_by(RateMaster.name.asc())

    async def add(self, rate: RateMaster) -> RateMaster:
        self.session.add(rate)
        await self.session.flush()
        return rate
