from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_masters
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.material import MaterialCreate, MaterialOut, MaterialUpdate
from app.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.post("", response_model=SuccessResponse[MaterialOut], status_code=status.HTTP_201_CREATED, summary="Create material")
async def create_material(
    payload: MaterialCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_masters)
):
    return SuccessResponse(message="Material created successfully", data=await MaterialService(db).create(payload, user))


@router.get("", response_model=SuccessResponse[PaginatedData[MaterialOut]], summary="List materials")
async def list_materials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(
        data=await MaterialService(db).list(
            page=page, page_size=page_size, search=search, category=category, brand=brand, is_active=is_active
        )
    )


@router.get("/{material_id}", response_model=SuccessResponse[MaterialOut], summary="Get material")
async def get_material(material_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await MaterialService(db).get(material_id))


@router.put("/{material_id}", response_model=SuccessResponse[MaterialOut], summary="Update material")
async def update_material(
    material_id: int,
    payload: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_masters),
):
    return SuccessResponse(
        message="Material updated successfully",
        data=await MaterialService(db).update(material_id, payload, user),
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate material")
async def delete_material(material_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    await MaterialService(db).delete(material_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
