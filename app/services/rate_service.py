from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.masters import RateMaster
from app.models.user import User
from app.repositories.rate_repository import RateRepository
from app.schemas.common import PaginatedData
from app.schemas.rate import RateCreate, RateOut, RateUpdate
from app.services.audit_service import AuditService
from app.utils.pagination import paginate


class RateService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = RateRepository(session)
        self.audit = AuditService(session)

    async def create(self, payload: RateCreate, user: User) -> RateOut:
        rate = RateMaster(**payload.model_dump())
        await self.repo.add(rate)
        await self.audit.log(
            user_id=user.id,
            action="rate.created",
            entity_type="rate_master",
            entity_id=rate.id,
            new_data={"name": rate.name, "rate": str(rate.rate)},
        )
        await self.session.commit()
        await self.session.refresh(rate)
        return RateOut.model_validate(rate)

    async def get(self, rate_id: int) -> RateOut:
        rate = await self.repo.get(rate_id)
        if not rate:
            raise NotFoundError("Rate not found")
        return RateOut.model_validate(rate)

    async def list(self, *, page: int, page_size: int, **filters) -> PaginatedData[RateOut]:
        items, data = await paginate(self.session, self.repo.list_query(**filters), page, page_size)
        return PaginatedData(
            items=[RateOut.model_validate(i) for i in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, rate_id: int, payload: RateUpdate, user: User) -> RateOut:
        rate = await self.repo.get(rate_id)
        if not rate:
            raise NotFoundError("Rate not found")
        old = {"rate": str(rate.rate)}
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(rate, key, value)
        await self.audit.log(
            user_id=user.id,
            action="rate.changed",
            entity_type="rate_master",
            entity_id=rate.id,
            old_data=old,
            new_data={"rate": str(rate.rate)},
        )
        await self.session.commit()
        await self.session.refresh(rate)
        return RateOut.model_validate(rate)

    async def delete(self, rate_id: int) -> None:
        rate = await self.repo.get(rate_id)
        if not rate:
            raise NotFoundError("Rate not found")
        rate.is_active = False
        await self.session.commit()
