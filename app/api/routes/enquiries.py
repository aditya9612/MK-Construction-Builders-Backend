"""Website enquiry routes. Public POST is unauthenticated; admin routes require admin."""

from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.cms_enums import EnquiryStatus
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.enquiry import (
    EnquiryAdminUpdate,
    EnquiryCreate,
    EnquiryListItem,
    EnquiryOut,
    EnquiryPublicOut,
    EnquiryUnreadCount,
)
from app.services.enquiry_service import EnquiryService

public_router = APIRouter(prefix="/enquiries", tags=["CMS Enquiries"])
admin_router = APIRouter(prefix="/admin/enquiries", tags=["CMS Enquiries Admin"])


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45] or None
    if request.client and request.client.host:
        return request.client.host[:45]
    return None


def _user_agent(request: Request) -> str | None:
    agent = request.headers.get("user-agent")
    if not agent:
        return None
    return agent.strip()[:500] or None


@public_router.post(
    "",
    response_model=SuccessResponse[EnquiryPublicOut],
    status_code=status.HTTP_201_CREATED,
    summary="Submit a website enquiry",
)
@public_router.post(
    "/",
    response_model=SuccessResponse[EnquiryPublicOut],
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_enquiry(
    payload: EnquiryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    data = await EnquiryService(db).create_public(
        payload,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return SuccessResponse(message="Enquiry submitted successfully", data=data)


@admin_router.get(
    "/unread-count",
    response_model=SuccessResponse[EnquiryUnreadCount],
    summary="Unread enquiry count for admin notifications",
)
async def unread_enquiry_count(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return SuccessResponse(data=await EnquiryService(db).unread_count())


@admin_router.get(
    "",
    response_model=SuccessResponse[PaginatedData[EnquiryListItem]],
    summary="List website enquiries (admin)",
)
async def list_admin_enquiries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: EnquiryStatus | None = None,
    is_read: bool | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await EnquiryService(db).list_admin(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        is_read=is_read,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@admin_router.get(
    "/{enquiry_id}",
    response_model=SuccessResponse[EnquiryOut],
    summary="Get enquiry by id (marks as read)",
)
async def get_admin_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return SuccessResponse(data=await EnquiryService(db).get_admin(enquiry_id))


@admin_router.patch(
    "/{enquiry_id}",
    response_model=SuccessResponse[EnquiryOut],
    summary="Update enquiry status or notes",
)
async def update_admin_enquiry(
    enquiry_id: int,
    payload: EnquiryAdminUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await EnquiryService(db).update(enquiry_id, payload)
    return SuccessResponse(message="Enquiry updated successfully", data=data)


@admin_router.post(
    "/{enquiry_id}/mark-unread",
    response_model=SuccessResponse[EnquiryOut],
    summary="Mark enquiry as unread",
)
async def mark_enquiry_unread(
    enquiry_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await EnquiryService(db).mark_unread(enquiry_id)
    return SuccessResponse(message="Enquiry marked unread", data=data)


@admin_router.delete(
    "/{enquiry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete enquiry",
)
async def delete_admin_enquiry(
    enquiry_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    await EnquiryService(db).delete(enquiry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


routers = (public_router, admin_router)
