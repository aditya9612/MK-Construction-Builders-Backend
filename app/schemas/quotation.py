from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import QuotationStatus
from app.schemas.common import ORMModel
from app.schemas.customer import CustomerOut
from app.schemas.project import ProjectOut
from app.schemas.quotation_item import (
    AdditionalItemIn,
    AdditionalItemOut,
    ConstructionItemIn,
    ConstructionItemOut,
    DoorItemIn,
    DoorItemOut,
    ElectricalItemIn,
    ElectricalItemOut,
    GraniteItemIn,
    MaterialItemIn,
    MaterialItemOut,
    PaintingItemIn,
    PaintingItemOut,
    PlumbingItemIn,
    PlumbingItemOut,
    TermItemIn,
    TermItemOut,
    TileItemIn,
    TileItemOut,
    WindowItemIn,
    WindowItemOut,
)


class CalculationSummary(BaseModel):
    construction_total: Decimal
    additional_total: Decimal
    electrical_total: Decimal
    plumbing_total: Decimal
    door_total: Decimal
    window_total: Decimal
    tile_total: Decimal
    granite_total: Decimal
    painting_total: Decimal
    subtotal: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    gst_percentage: Decimal
    gst_amount: Decimal
    grand_total: Decimal


class QuotationCreate(BaseModel):
    customer_id: int
    project_id: int
    quotation_date: date
    notes: str | None = None
    discount_percentage: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    gst_percentage: Decimal = Field(default=Decimal("18.00"), ge=0)
    construction_items: list[ConstructionItemIn] = Field(default_factory=list)
    additional_items: list[AdditionalItemIn] = Field(default_factory=list)
    electrical_items: list[ElectricalItemIn] = Field(default_factory=list)
    plumbing_items: list[PlumbingItemIn] = Field(default_factory=list)
    doors: list[DoorItemIn] = Field(default_factory=list)
    windows: list[WindowItemIn] = Field(default_factory=list)
    tiles: list[TileItemIn] = Field(default_factory=list)
    granite: list[GraniteItemIn] = Field(default_factory=list)
    painting: list[PaintingItemIn] = Field(default_factory=list)
    materials: list[MaterialItemIn] = Field(default_factory=list)
    terms: list[TermItemIn] = Field(default_factory=list)


class QuotationUpdate(QuotationCreate):
    pass


class QuotationListItem(ORMModel):
    id: int
    quotation_number: str
    customer_id: int
    project_id: int
    quotation_date: date
    status: str
    grand_total: Decimal
    created_at: datetime
    customer: CustomerOut | None = None
    project: ProjectOut | None = None


class QuotationOut(ORMModel):
    id: int
    quotation_number: str
    customer_id: int
    project_id: int
    quotation_date: date
    status: str
    subtotal: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    gst_percentage: Decimal
    gst_amount: Decimal
    grand_total: Decimal
    notes: str | None
    created_by: int | None
    updated_by: int | None
    created_at: datetime
    updated_at: datetime
    customer: CustomerOut | None = None
    project: ProjectOut | None = None
    construction_items: list[ConstructionItemOut] = Field(default_factory=list)
    additional_items: list[AdditionalItemOut] = Field(default_factory=list)
    electrical_items: list[ElectricalItemOut] = Field(default_factory=list)
    plumbing_items: list[PlumbingItemOut] = Field(default_factory=list)
    doors: list[DoorItemOut] = Field(default_factory=list)
    windows: list[WindowItemOut] = Field(default_factory=list)
    tiles: list[TileItemOut] = Field(default_factory=list)
    granite: list[TileItemOut] = Field(default_factory=list)
    painting: list[PaintingItemOut] = Field(default_factory=list)
    materials: list[MaterialItemOut] = Field(default_factory=list)
    terms: list[TermItemOut] = Field(default_factory=list)
    calculation_summary: CalculationSummary | None = None


class QuotationStatusAction(BaseModel):
    notes: str | None = None
