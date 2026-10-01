from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TermCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    category: str = Field(default="GENERAL", max_length=50)
    is_default: bool = False
    is_active: bool = True


class TermUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class TermOut(ORMModel):
    id: int
    title: str
    content: str
    category: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
