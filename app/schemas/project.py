from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    customer_id: int
    project_name: str = Field(min_length=1, max_length=200)
    site_address: str | None = None
    plot_area: Decimal | None = Field(default=None, ge=0)
    construction_area: Decimal | None = Field(default=None, ge=0)
    number_of_floors: int | None = Field(default=None, ge=0)
    floor_type: str | None = Field(default=None, max_length=50)
    start_date: date | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    notes: str | None = None


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=200)
    site_address: str | None = None
    plot_area: Decimal | None = Field(default=None, ge=0)
    construction_area: Decimal | None = Field(default=None, ge=0)
    number_of_floors: int | None = Field(default=None, ge=0)
    floor_type: str | None = None
    start_date: date | None = None
    status: ProjectStatus | None = None
    notes: str | None = None


class ProjectOut(ORMModel):
    id: int
    project_code: str
    customer_id: int
    project_name: str
    site_address: str | None
    plot_area: Decimal | None
    construction_area: Decimal | None
    number_of_floors: int | None
    floor_type: str | None
    start_date: date | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime
