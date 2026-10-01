from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import MaterialCategory
from app.schemas.common import ORMModel


class MaterialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: MaterialCategory
    brand: str | None = None
    specification: str | None = None
    unit: str = Field(min_length=1, max_length=30)
    description: str | None = None
    is_active: bool = True


class MaterialUpdate(BaseModel):
    name: str | None = None
    category: MaterialCategory | None = None
    brand: str | None = None
    specification: str | None = None
    unit: str | None = None
    description: str | None = None
    is_active: bool | None = None


class MaterialOut(ORMModel):
    id: int
    name: str
    category: str
    brand: str | None
    specification: str | None
    unit: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
