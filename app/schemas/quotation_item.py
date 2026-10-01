from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import AdditionalCategory, PaintingCategory
from app.schemas.common import ORMModel


class MoneyItemIn(BaseModel):
    quantity: Decimal = Field(ge=0)
    unit: str = Field(default="sqft", max_length=30)
    rate: Decimal = Field(ge=0)
    sort_order: int = 0


class ConstructionItemIn(MoneyItemIn):
    rate_master_id: int | None = None
    description: str = Field(min_length=1, max_length=255)


class AdditionalItemIn(MoneyItemIn):
    category: AdditionalCategory
    description: str = Field(min_length=1, max_length=255)


class ElectricalItemIn(MoneyItemIn):
    area: str | None = Field(default=None, max_length=100)
    item_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="nos", max_length=30)


class PlumbingItemIn(MoneyItemIn):
    item_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="nos", max_length=30)


class DoorItemIn(MoneyItemIn):
    item_id: int | None = None
    item_name: str = Field(min_length=1, max_length=200)
    unit: str = Field(default="nos", max_length=30)


class WindowItemIn(BaseModel):
    item_id: int | None = None
    item_name: str = Field(min_length=1, max_length=200)
    length: Decimal = Field(gt=0)
    width: Decimal = Field(gt=0)
    unit: str = Field(default="sqft", max_length=30)
    rate: Decimal = Field(ge=0)
    sort_order: int = 0


class TileItemIn(BaseModel):
    item_id: int | None = None
    category: str = Field(default="TILE", max_length=40)
    description: str = Field(min_length=1, max_length=255)
    area: Decimal = Field(ge=0)
    unit: str = Field(default="sqft", max_length=30)
    rate: Decimal = Field(ge=0)
    sort_order: int = 0


class GraniteItemIn(TileItemIn):
    category: str = Field(default="GRANITE", max_length=40)


class PaintingItemIn(BaseModel):
    category: PaintingCategory
    description: str = Field(min_length=1, max_length=255)
    area: Decimal = Field(ge=0)
    unit: str = Field(default="sqft", max_length=30)
    rate: Decimal = Field(ge=0)
    sort_order: int = 0


class MaterialItemIn(BaseModel):
    material_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    category: str | None = None
    brand: str | None = None
    specification: str | None = None
    unit: str | None = None
    sort_order: int = 0


class TermItemIn(BaseModel):
    term_id: int | None = None
    term_order: int = 0
    custom_content: str | None = None


class ConstructionItemOut(ORMModel):
    id: int
    rate_master_id: int | None
    description: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class AdditionalItemOut(ORMModel):
    id: int
    category: str
    description: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class ElectricalItemOut(ORMModel):
    id: int
    area: str | None
    item_name: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class PlumbingItemOut(ORMModel):
    id: int
    item_name: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class DoorItemOut(ORMModel):
    id: int
    item_id: int | None
    item_name: str
    quantity: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class WindowItemOut(ORMModel):
    id: int
    item_id: int | None
    item_name: str
    length: Decimal
    width: Decimal
    area: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class TileItemOut(ORMModel):
    id: int
    item_id: int | None
    category: str
    description: str
    area: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class PaintingItemOut(ORMModel):
    id: int
    category: str
    description: str
    area: Decimal
    unit: str
    rate: Decimal
    amount: Decimal
    sort_order: int


class MaterialItemOut(ORMModel):
    id: int
    material_id: int | None
    name: str
    category: str | None
    brand: str | None
    specification: str | None
    unit: str | None
    sort_order: int


class TermItemOut(ORMModel):
    id: int
    term_id: int | None
    term_order: int
    custom_content: str | None
