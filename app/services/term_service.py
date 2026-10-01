from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.term import Term
from app.schemas.common import PaginatedData
from app.schemas.term import TermCreate, TermOut, TermUpdate
from app.utils.pagination import paginate
from sqlalchemy import or_, select


class TermService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, payload: TermCreate) -> TermOut:
        term = Term(**payload.model_dump())
        self.session.add(term)
        await self.session.commit()
        await self.session.refresh(term)
        return TermOut.model_validate(term)

    async def get(self, term_id: int) -> TermOut:
        term = await self.session.get(Term, term_id)
        if not term:
            raise NotFoundError("Term not found")
        return TermOut.model_validate(term)

    async def list(self, *, page: int, page_size: int, search: str | None = None, is_active: bool | None = None) -> PaginatedData[TermOut]:
        stmt = select(Term)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(or_(Term.title.ilike(like), Term.content.ilike(like)))
        if is_active is not None:
            stmt = stmt.where(Term.is_active.is_(is_active))
        stmt = stmt.order_by(Term.id.asc())
        items, data = await paginate(self.session, stmt, page, page_size)
        return PaginatedData(
            items=[TermOut.model_validate(i) for i in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, term_id: int, payload: TermUpdate) -> TermOut:
        term = await self.session.get(Term, term_id)
        if not term:
            raise NotFoundError("Term not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(term, key, value)
        await self.session.commit()
        await self.session.refresh(term)
        return TermOut.model_validate(term)

    async def delete(self, term_id: int) -> None:
        term = await self.session.get(Term, term_id)
        if not term:
            raise NotFoundError("Term not found")
        term.is_active = False
        await self.session.commit()
