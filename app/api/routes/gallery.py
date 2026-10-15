"""CMS gallery routes. Public GETs are unauthenticated and published-only.

Not registered in ``app.api.router`` until integration approval.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_masters
from app.core.database import get_db
from app.models.cms_enums import GalleryCategory, PublicationStatus
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.gallery import GalleryItemCreate, GalleryItemOut, GalleryItemUpdate
from app.services.gallery_service import GalleryService

public_router = APIRouter(prefix="/gallery", tags=["CMS Gallery"])
admin_router = APIRouter(prefix="/admin/gallery", tags=["CMS Gallery Admin"])


@public_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[GalleryItemOut]],
    summary="List published gallery items",
)
async def list_published_gallery(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: GalleryCategory | None = None,
    search: str | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    data = await GalleryService(db).list_public(
        page=page,
        page_size=page_size,
        category=category,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@admin_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[GalleryItemOut]],
    summary="List all gallery items (admin)",
)
async def list_admin_gallery(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: GalleryCategory | None = None,
    search: str | None = None,
    publication_status: PublicationStatus | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await GalleryService(db).list_admin(
        page=page,
        page_size=page_size,
        category=category,
        search=search,
        publication_status=publication_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)



@admin_router.get(
    "/{item_id}",
    response_model=SuccessResponse[GalleryItemOut],
    summary="Get gallery item by id (admin)",
)
async def get_admin_gallery_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    return SuccessResponse(data=await GalleryService(db).get_admin(item_id))


@admin_router.post(
    "",
    response_model=SuccessResponse[GalleryItemOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create gallery item",
)
async def create_gallery_item(
    payload: GalleryItemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await GalleryService(db).create(payload)
    return SuccessResponse(message="Gallery item created successfully", data=data)


@admin_router.put(
    "/{item_id}",
    response_model=SuccessResponse[GalleryItemOut],
    summary="Update gallery item",
)
async def update_gallery_item(
    item_id: int,
    payload: GalleryItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await GalleryService(db).update(item_id, payload)
    return SuccessResponse(message="Gallery item updated successfully", data=data)


@admin_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete gallery item",
)
async def delete_gallery_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    await GalleryService(db).delete(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


routers = (public_router, admin_router)
