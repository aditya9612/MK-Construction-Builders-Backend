from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_masters
from app.core.database import get_db
from app.models.masters import ElectricalMaster
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.master import MasterCreate, MasterOut, MasterUpdate
from app.services.master_service import MasterService

router = APIRouter(prefix="/electrical", tags=["Electrical"])


def service(db: AsyncSession) -> MasterService:
    return MasterService(db, ElectricalMaster)


@router.post("", response_model=SuccessResponse[MasterOut], status_code=status.HTTP_201_CREATED, summary="Create electrical item")
async def create_item(payload: MasterCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    return SuccessResponse(message="Electrical item created", data=await service(db).create(payload))


@router.get("", response_model=SuccessResponse[PaginatedData[MasterOut]], summary="List electrical items")
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await service(db).list(page=page, page_size=page_size, search=search, category=category, is_active=is_active))


@router.get("/{item_id}", response_model=SuccessResponse[MasterOut], summary="Get electrical item")
async def get_item(item_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await service(db).get(item_id))


@router.put("/{item_id}", response_model=SuccessResponse[MasterOut], summary="Update electrical item")
async def update_item(item_id: int, payload: MasterUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    return SuccessResponse(message="Electrical item updated", data=await service(db).update(item_id, payload))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate electrical item")
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    await service(db).delete(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
