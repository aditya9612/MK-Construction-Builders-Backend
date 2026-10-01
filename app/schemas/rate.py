from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    unit: str = Field(min_length=1, max_length=30)
    rate: Decimal = Field(ge=0)
    description: str | None = None
    is_active: bool = True
    effective_from: date | None = None
    effective_to: date | None = None


class RateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    rate: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class RateOut(ORMModel):
    id: int
    name: str
    category: str
    unit: str
    rate: Decimal
    description: str | None
    is_active: bool
    effective_from: date | None
    effective_to: date | None
    created_at: datetime
    updated_at: datetime
