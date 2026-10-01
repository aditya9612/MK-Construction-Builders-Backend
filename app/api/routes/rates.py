from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_masters
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.rate import RateCreate, RateOut, RateUpdate
from app.services.rate_service import RateService

router = APIRouter(prefix="/rates", tags=["Rates"])


@router.post("", response_model=SuccessResponse[RateOut], status_code=status.HTTP_201_CREATED, summary="Create rate")
async def create_rate(payload: RateCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_masters)):
    return SuccessResponse(message="Rate created successfully", data=await RateService(db).create(payload, user))


@router.get("", response_model=SuccessResponse[PaginatedData[RateOut]], summary="List rates")
async def list_rates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    unit: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(
        data=await RateService(db).list(
            page=page, page_size=page_size, search=search, category=category, unit=unit, is_active=is_active
        )
    )


@router.get("/{rate_id}", response_model=SuccessResponse[RateOut], summary="Get rate")
async def get_rate(rate_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await RateService(db).get(rate_id))


@router.put("/{rate_id}", response_model=SuccessResponse[RateOut], summary="Update rate")
async def update_rate(
    rate_id: int,
    payload: RateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_masters),
):
    return SuccessResponse(message="Rate updated successfully", data=await RateService(db).update(rate_id, payload, user))


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate rate")
async def delete_rate(rate_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    await RateService(db).delete(rate_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
