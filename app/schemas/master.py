from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class MasterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="GENERAL", max_length=50)
    unit: str = Field(default="nos", max_length=30)
    rate: Decimal = Field(ge=0)
    description: str | None = None
    is_active: bool = True


class MasterUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    rate: Decimal | None = Field(default=None, ge=0)
    description: str | None = None
    is_active: bool | None = None


class MasterOut(ORMModel):
    id: int
    name: str
    category: str
    unit: str
    rate: Decimal
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
