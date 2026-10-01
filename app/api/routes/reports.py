from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/quotation-summary", response_model=SuccessResponse[dict], summary="Quotation summary report")
async def quotation_summary(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await ReportService(db).quotation_summary(date_from, date_to))


@router.get("/monthly", response_model=SuccessResponse[list], summary="Monthly quotation report")
async def monthly_report(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await ReportService(db).monthly(date_from, date_to))


@router.get("/customer-wise", response_model=SuccessResponse[list], summary="Customer-wise quotation report")
async def customer_wise(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await ReportService(db).customer_wise(date_from, date_to))


@router.get("/status-wise", response_model=SuccessResponse[list], summary="Status-wise quotation report")
async def status_wise(
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await ReportService(db).status_wise(date_from, date_to))
