"""CMS website service routes. Public GETs are unauthenticated and published-only."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.cms_enums import PublicationStatus
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.website_service import (
    WebsiteServiceCreate,
    WebsiteServiceOut,
    WebsiteServiceUpdate,
)
from app.services.website_service_service import WebsiteServiceService

public_router = APIRouter(prefix="/services", tags=["CMS Services"])
admin_router = APIRouter(prefix="/admin/services", tags=["CMS Services Admin"])


@public_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[WebsiteServiceOut]],
    summary="List published website services",
)
async def list_published_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    data = await WebsiteServiceService(db).list_public(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@public_router.get(
    "/{slug}",
    response_model=SuccessResponse[WebsiteServiceOut],
    summary="Get a published website service by slug",
)
async def get_published_service(slug: str, db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await WebsiteServiceService(db).get_public_by_slug(slug))


@admin_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[WebsiteServiceOut]],
    summary="List all website services (admin)",
)
async def list_admin_services(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    publication_status: PublicationStatus | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await WebsiteServiceService(db).list_admin(
        page=page,
        page_size=page_size,
        search=search,
        publication_status=publication_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@admin_router.get(
    "/{service_id}",
    response_model=SuccessResponse[WebsiteServiceOut],
    summary="Get website service by id (admin)",
)
async def get_admin_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return SuccessResponse(data=await WebsiteServiceService(db).get_admin(service_id))


@admin_router.post(
    "",
    response_model=SuccessResponse[WebsiteServiceOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create website service",
)
async def create_service(
    payload: WebsiteServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await WebsiteServiceService(db).create(payload)
    return SuccessResponse(message="Service created successfully", data=data)


@admin_router.put(
    "/{service_id}",
    response_model=SuccessResponse[WebsiteServiceOut],
    summary="Update website service",
)
async def update_service(
    service_id: int,
    payload: WebsiteServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await WebsiteServiceService(db).update(service_id, payload)
    return SuccessResponse(message="Service updated successfully", data=data)


@admin_router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete website service",
)
async def delete_service(
    service_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await WebsiteServiceService(db).delete(service_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


routers = (public_router, admin_router)
