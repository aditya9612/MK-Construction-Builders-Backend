from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class CompanySettingsUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=200)
    logo_url: str | None = None
    address: str | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    gst_number: str | None = None
    quotation_prefix: str | None = Field(default=None, max_length=20)
    default_gst: Decimal | None = Field(default=None, ge=0)
    bank_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None
    signature_url: str | None = None


class CompanySettingsOut(ORMModel):
    id: int
    company_name: str
    logo_url: str | None
    address: str | None
    mobile: str | None
    email: str | None
    gst_number: str | None
    quotation_prefix: str
    default_gst: Decimal
    bank_name: str | None
    account_number: str | None
    ifsc_code: str | None
    signature_url: str | None
    created_at: datetime
    updated_at: datetime
