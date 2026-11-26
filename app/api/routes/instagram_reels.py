"""Instagram Reels CMS routes.

Public GET returns published reels only when the section is enabled.
All admin routes are protected by ``require_admin``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.instagram_reel import (
    InstagramReelCreate,
    InstagramReelOrderUpdate,
    InstagramReelOut,
    InstagramReelPublicListOut,
    InstagramReelPublishUpdate,
    InstagramReelUpdate,
    InstagramSectionSettingsOut,
    InstagramSectionSettingsUpdate,
)
from app.services.instagram_reel_service import InstagramReelService

public_router = APIRouter(prefix="/public/instagram-reels", tags=["CMS Instagram Reels"])
admin_router = APIRouter(prefix="/admin/instagram-reels", tags=["CMS Instagram Reels Admin"])


# ==============================================================================
# Public API (Unauthenticated)
# ==============================================================================


@public_router.get(
    "",
    response_model=SuccessResponse[InstagramReelPublicListOut],
    summary="List published Instagram reels and section status",
)
async def list_public_instagram_reels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    data = await InstagramReelService(db).list_public(page=page, page_size=page_size)
    return SuccessResponse(data=data)


# ==============================================================================
# Admin APIs (Protected by require_admin)
# Static /settings routes are registered before dynamic /{id} routes.
# ==============================================================================


@admin_router.get(
    "/settings",
    response_model=SuccessResponse[InstagramSectionSettingsOut],
    summary="Get Instagram Reels section settings (admin)",
)
async def get_instagram_section_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).get_settings()
    return SuccessResponse(data=data)


@admin_router.put(
    "/settings",
    response_model=SuccessResponse[InstagramSectionSettingsOut],
    summary="Update Instagram Reels section settings (admin)",
)
async def update_instagram_section_settings(
    payload: InstagramSectionSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).update_settings(payload)
    return SuccessResponse(message="Instagram section settings updated successfully", data=data)


@admin_router.post(
    "",
    response_model=SuccessResponse[InstagramReelOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create Instagram reel (admin)",
)
async def create_instagram_reel(
    payload: InstagramReelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).create(payload)
    return SuccessResponse(message="Instagram reel created successfully", data=data)


@admin_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[InstagramReelOut]],
    summary="List all Instagram reels (admin)",
)
async def list_admin_instagram_reels(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_published: bool | None = None,
    sort_by: str = Query("display_order"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).list_admin(
        page=page,
        page_size=page_size,
        search=search,
        is_published=is_published,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@admin_router.get(
    "/{id}",
    response_model=SuccessResponse[InstagramReelOut],
    summary="Get Instagram reel by id (admin)",
)
async def get_admin_instagram_reel(
    id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).get_admin(id)
    return SuccessResponse(data=data)


@admin_router.put(
    "/{id}",
    response_model=SuccessResponse[InstagramReelOut],
    summary="Update Instagram reel (admin)",
)
async def update_instagram_reel(
    id: int,
    payload: InstagramReelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).update(id, payload)
    return SuccessResponse(message="Instagram reel updated successfully", data=data)


@admin_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Instagram reel (admin)",
)
async def delete_instagram_reel(
    id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await InstagramReelService(db).delete(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.patch(
    "/{id}/publish",
    response_model=SuccessResponse[InstagramReelOut],
    summary="Update Instagram reel publish status (admin)",
)
async def set_instagram_reel_publish_status(
    id: int,
    payload: InstagramReelPublishUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).set_publish_status(id, payload.is_published)
    return SuccessResponse(
        message=f"Instagram reel {'published' if payload.is_published else 'unpublished'} successfully",
        data=data,
    )


@admin_router.patch(
    "/{id}/order",
    response_model=SuccessResponse[InstagramReelOut],
    summary="Update Instagram reel display order (admin)",
)
async def set_instagram_reel_display_order(
    id: int,
    payload: InstagramReelOrderUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await InstagramReelService(db).set_display_order(id, payload.display_order)
    return SuccessResponse(
        message="Instagram reel display order updated successfully",
        data=data,
    )


routers = (public_router, admin_router)
