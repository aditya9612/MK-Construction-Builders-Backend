from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_approve, require_write
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.quotation import (
    CalculationSummary,
    QuotationCreate,
    QuotationListItem,
    QuotationOut,
    QuotationUpdate,
)
from app.services.quotation_service import QuotationService

router = APIRouter(prefix="/quotations", tags=["Quotations"])


@router.post("", response_model=SuccessResponse[QuotationOut], status_code=status.HTTP_201_CREATED, summary="Create quotation")
async def create_quotation(
    payload: QuotationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_write),
):
    data = await QuotationService(db).create(payload, user)
    return SuccessResponse(message="Quotation created successfully", data=data)


@router.get("", response_model=SuccessResponse[PaginatedData[QuotationListItem]], summary="List quotations")
async def list_quotations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    customer_id: int | None = None,
    project_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = await QuotationService(db).list(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        customer_id=customer_id,
        project_id=project_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@router.get("/{quotation_id}", response_model=SuccessResponse[QuotationOut], summary="Get quotation")
async def get_quotation(quotation_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await QuotationService(db).get(quotation_id))


@router.put("/{quotation_id}", response_model=SuccessResponse[QuotationOut], summary="Update quotation")
async def update_quotation(
    quotation_id: int,
    payload: QuotationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_write),
):
    data = await QuotationService(db).update(quotation_id, payload, user)
    return SuccessResponse(message="Quotation updated successfully", data=data)


@router.delete("/{quotation_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete quotation")
async def delete_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_write),
):
    await QuotationService(db).delete(quotation_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{quotation_id}/duplicate", response_model=SuccessResponse[QuotationOut], status_code=status.HTTP_201_CREATED, summary="Duplicate quotation")
async def duplicate_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_write),
):
    data = await QuotationService(db).duplicate(quotation_id, user)
    return SuccessResponse(message="Quotation duplicated successfully", data=data)


@router.post("/{quotation_id}/send", response_model=SuccessResponse[QuotationOut], summary="Send quotation")
async def send_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_write),
):
    return SuccessResponse(message="Quotation sent", data=await QuotationService(db).send(quotation_id, user))


@router.post("/{quotation_id}/approve", response_model=SuccessResponse[QuotationOut], summary="Approve quotation")
async def approve_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_approve),
):
    return SuccessResponse(message="Quotation approved", data=await QuotationService(db).approve(quotation_id, user))


@router.post("/{quotation_id}/reject", response_model=SuccessResponse[QuotationOut], summary="Reject quotation")
async def reject_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_approve),
):
    return SuccessResponse(message="Quotation rejected", data=await QuotationService(db).reject(quotation_id, user))


@router.post("/{quotation_id}/expire", response_model=SuccessResponse[QuotationOut], summary="Expire quotation")
async def expire_quotation(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_approve),
):
    return SuccessResponse(message="Quotation expired", data=await QuotationService(db).expire(quotation_id, user))


@router.get("/{quotation_id}/summary", response_model=SuccessResponse[CalculationSummary], summary="Quotation calculation summary")
async def quotation_summary(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await QuotationService(db).summary(quotation_id))


@router.get("/{quotation_id}/preview", response_model=SuccessResponse[dict], summary="Print-ready quotation preview")
async def quotation_preview(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await QuotationService(db).preview(quotation_id))
