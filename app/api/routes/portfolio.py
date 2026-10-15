"""CMS portfolio routes. Public GETs are unauthenticated and published-only.

Not registered in ``app.api.router`` until integration approval.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_masters
from app.core.database import get_db
from app.models.cms_enums import (
    PortfolioDisplayStatus,
    PortfolioProjectType,
    PublicationStatus,
)
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.portfolio import (
    PortfolioGalleryAttach,
    PortfolioGalleryDetach,
    PortfolioProjectCreate,
    PortfolioProjectListItemOut,
    PortfolioProjectOut,
    PortfolioProjectUpdate,
)
from app.services.portfolio_service import PortfolioService

public_router = APIRouter(prefix="/portfolio", tags=["CMS Portfolio"])
admin_router = APIRouter(prefix="/admin/portfolio", tags=["CMS Portfolio Admin"])


@public_router.get(
    "/projects",
    response_model=SuccessResponse[PaginatedData[PortfolioProjectListItemOut]],
    summary="List published portfolio projects",
)
async def list_published_portfolio_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    type: PortfolioProjectType | None = Query(default=None, alias="type"),
    status_filter: PortfolioDisplayStatus | None = Query(default=None, alias="status"),
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
):
    data = await PortfolioService(db).list_public(
        page=page,
        page_size=page_size,
        search=search,
        project_type=type,
        status=status_filter,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@public_router.get(
    "/projects/{slug}",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Get a published portfolio project by slug",
)
async def get_published_portfolio_project(slug: str, db: AsyncSession = Depends(get_db)):
    return SuccessResponse(data=await PortfolioService(db).get_public_by_slug(slug))


@admin_router.get(
    "/projects",
    response_model=SuccessResponse[PaginatedData[PortfolioProjectListItemOut]],
    summary="List all portfolio projects (admin)",
)
async def list_admin_portfolio_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    type: PortfolioProjectType | None = Query(default=None, alias="type"),
    status_filter: PortfolioDisplayStatus | None = Query(default=None, alias="status"),
    publication_status: PublicationStatus | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).list_admin(
        page=page,
        page_size=page_size,
        search=search,
        project_type=type,
        status=status_filter,
        publication_status=publication_status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)



@admin_router.get(
    "/projects/{project_id}",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Get portfolio project by id (admin)",
)
async def get_admin_portfolio_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    return SuccessResponse(data=await PortfolioService(db).get_admin(project_id))


@admin_router.post(
    "/projects",
    response_model=SuccessResponse[PortfolioProjectOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create portfolio project",
)
async def create_portfolio_project(
    payload: PortfolioProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).create(payload)
    return SuccessResponse(message="Portfolio project created successfully", data=data)


@admin_router.put(
    "/projects/{project_id}",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Update portfolio project",
)
async def update_portfolio_project(
    project_id: int,
    payload: PortfolioProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).update(project_id, payload)
    return SuccessResponse(message="Portfolio project updated successfully", data=data)


@admin_router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete portfolio project",
)
async def delete_portfolio_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    await PortfolioService(db).delete(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post(
    "/projects/{project_id}/gallery",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Attach media to portfolio project gallery",
)
async def attach_portfolio_gallery(
    project_id: int,
    payload: PortfolioGalleryAttach,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).attach_gallery(project_id, payload)
    return SuccessResponse(message="Gallery images attached successfully", data=data)


@admin_router.delete(
    "/projects/{project_id}/gallery",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Detach media from portfolio project gallery",
)
async def detach_portfolio_gallery(
    project_id: int,
    payload: PortfolioGalleryDetach,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).detach_gallery(project_id, payload)
    return SuccessResponse(message="Gallery images detached successfully", data=data)


@admin_router.delete(
    "/projects/{project_id}/gallery/{media_id}",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Detach a media item from portfolio project gallery by media ID",
)
async def detach_portfolio_gallery_item(
    project_id: int,
    media_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).detach_gallery_media(project_id, media_id)
    return SuccessResponse(message="Gallery image detached successfully", data=data)


@admin_router.post(
    "/projects/{project_id}/gallery/detach",
    response_model=SuccessResponse[PortfolioProjectOut],
    summary="Detach media from portfolio project gallery (POST alternative)",
)
async def detach_portfolio_gallery_post(
    project_id: int,
    payload: PortfolioGalleryDetach,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_masters),
):
    data = await PortfolioService(db).detach_gallery(project_id, payload)
    return SuccessResponse(message="Gallery images detached successfully", data=data)


routers = (public_router, admin_router)

