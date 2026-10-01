from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.schemas.common import PaginatedData
from app.schemas.master import MasterCreate, MasterOut, MasterUpdate
from app.utils.pagination import paginate


class MasterService:
    def __init__(self, session: AsyncSession, model):
        self.session = session
        self.model = model

    def list_query(self, search: str | None = None, category: str | None = None, is_active: bool | None = None) -> Select:
        stmt = select(self.model)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(self.model.name.ilike(like), self.model.description.ilike(like)))
        if category:
            stmt = stmt.where(self.model.category == category)
        if is_active is not None:
            stmt = stmt.where(self.model.is_active.is_(is_active))
        return stmt.order_by(self.model.name.asc())

    async def create(self, payload: MasterCreate) -> MasterOut:
        record = self.model(**payload.model_dump())
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return MasterOut.model_validate(record)

    async def get(self, record_id: int) -> MasterOut:
        record = await self.session.get(self.model, record_id)
        if not record:
            raise NotFoundError("Record not found")
        return MasterOut.model_validate(record)

    async def list(self, *, page: int, page_size: int, **filters) -> PaginatedData[MasterOut]:
        items, data = await paginate(self.session, self.list_query(**filters), page, page_size)
        return PaginatedData(
            items=[MasterOut.model_validate(i) for i in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, record_id: int, payload: MasterUpdate) -> MasterOut:
        record = await self.session.get(self.model, record_id)
        if not record:
            raise NotFoundError("Record not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.session.commit()
        await self.session.refresh(record)
        return MasterOut.model_validate(record)

    async def delete(self, record_id: int) -> None:
        record = await self.session.get(self.model, record_id)
        if not record:
            raise NotFoundError("Record not found")
        record.is_active = False
        await self.session.commit()
