from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.quotation import QuotationListItem


class StatusCount(BaseModel):
    status: str
    count: int
    value: Decimal


class CustomerValue(BaseModel):
    customer_id: int
    customer_name: str
    quotation_count: int
    total_value: Decimal


class DashboardSummary(BaseModel):
    total_quotations: int
    draft_quotations: int
    sent_quotations: int
    approved_quotations: int
    rejected_quotations: int
    expired_quotations: int
    total_quotation_value: Decimal
    approved_quotation_value: Decimal
    monthly_quotation_value: Decimal
    monthly_quotation_count: int
    recent_quotations: list[QuotationListItem]
    quotation_status_distribution: list[StatusCount]
    customer_wise_quotation_value: list[CustomerValue]


class MonthlyReportRow(BaseModel):
    year: int
    month: int
    quotation_count: int
    total_value: Decimal
    approved_value: Decimal


class DateFilter(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
