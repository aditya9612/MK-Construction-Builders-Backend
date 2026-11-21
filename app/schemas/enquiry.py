"""Pydantic schemas for website enquiries."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.cms_enums import EnquiryStatus
from app.schemas.common import ORMModel
from app.utils.validators import validate_indian_mobile

MESSAGE_PREVIEW_LEN = 120


def _blank_to_none(value: str | None, *, max_length: int) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) > max_length:
        raise ValueError(f"must be at most {max_length} characters")
    return text


class EnquiryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    mobile: str
    email: EmailStr | None = None
    project_type: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    construction_area: str | None = Field(default=None, max_length=120)
    message: str | None = Field(default=None, max_length=4000)

    @field_validator("name")
    @classmethod
    def name_ok(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("Name must be at least 2 characters")
        return name

    @field_validator("mobile")
    @classmethod
    def mobile_ok(cls, value: str) -> str:
        return validate_indian_mobile(value)

    @field_validator("email", mode="before")
    @classmethod
    def email_ok(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("project_type")
    @classmethod
    def project_type_ok(cls, value: str | None) -> str | None:
        return _blank_to_none(value, max_length=120)

    @field_validator("location")
    @classmethod
    def location_ok(cls, value: str | None) -> str | None:
        return _blank_to_none(value, max_length=255)

    @field_validator("construction_area")
    @classmethod
    def area_ok(cls, value: str | None) -> str | None:
        return _blank_to_none(value, max_length=120)

    @field_validator("message")
    @classmethod
    def message_ok(cls, value: str | None) -> str | None:
        return _blank_to_none(value, max_length=4000)


class EnquiryAdminUpdate(BaseModel):
    status: EnquiryStatus | None = None
    admin_notes: str | None = None
    is_read: bool | None = None

    @field_validator("admin_notes")
    @classmethod
    def notes_ok(cls, value: str | None) -> str | None:
        return _blank_to_none(value, max_length=4000)


class EnquiryPublicOut(ORMModel):
    id: int
    created_at: datetime


class EnquiryListItem(ORMModel):
    id: int
    name: str
    mobile: str
    email: str | None
    project_type: str | None
    location: str | None
    construction_area: str | None
    message_preview: str | None
    status: str
    is_read: bool
    created_at: datetime


class EnquiryOut(ORMModel):
    id: int
    name: str
    mobile: str
    email: str | None
    project_type: str | None
    location: str | None
    construction_area: str | None
    message: str | None
    status: str
    is_read: bool
    source: str
    ip_address: str | None
    user_agent: str | None
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime


class EnquiryUnreadCount(BaseModel):
    unread_count: int


def message_preview(message: str | None) -> str | None:
    if not message:
        return None
    text = message.strip()
    if len(text) <= MESSAGE_PREVIEW_LEN:
        return text
    return text[: MESSAGE_PREVIEW_LEN - 1] + "…"
