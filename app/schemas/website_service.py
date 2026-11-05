"""Pydantic schemas for website CMS services."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.cms_enums import PublicationStatus
from app.schemas.common import ORMModel
from app.schemas.uploaded_media import MediaRefOut

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_slug(value: str) -> str:
    slug = value.strip().lower()
    if not slug:
        raise ValueError("Slug must not be empty")
    if len(slug) > 220:
        raise ValueError("Slug must be at most 220 characters")
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            "Slug must be lowercase alphanumeric words separated by single hyphens"
        )
    return slug


def _normalize_features(value: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in value:
        text = item.strip()
        if not text:
            raise ValueError("features must not contain empty strings")
        if len(text) > 200:
            raise ValueError("each feature must be at most 200 characters")
        cleaned.append(text)
    return cleaned


class WebsiteServiceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=220)
    description: str | None = None
    features: list[str] = Field(default_factory=list)
    image_id: int = Field(ge=1)
    display_order: int = Field(default=0, ge=0)
    publication_status: PublicationStatus = PublicationStatus.DRAFT

    @field_validator("slug")
    @classmethod
    def slug_ok(cls, value: str) -> str:
        return _normalize_slug(value)

    @field_validator("title")
    @classmethod
    def title_ok(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Title must not be empty")
        return title

    @field_validator("features")
    @classmethod
    def features_ok(cls, value: list[str]) -> list[str]:
        return _normalize_features(value)


class WebsiteServiceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=220)
    description: str | None = None
    features: list[str] | None = None
    image_id: int | None = Field(default=None, ge=1)
    display_order: int | None = Field(default=None, ge=0)
    publication_status: PublicationStatus | None = None

    @field_validator("slug")
    @classmethod
    def slug_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _normalize_slug(value)

    @field_validator("title")
    @classmethod
    def title_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        title = value.strip()
        if not title:
            raise ValueError("Title must not be empty")
        return title

    @field_validator("features")
    @classmethod
    def features_ok(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return _normalize_features(value)


class WebsiteServiceOut(ORMModel):
    id: int
    title: str
    slug: str
    description: str | None
    features: list[str] = Field(default_factory=list)
    image_id: int
    image: MediaRefOut | None = None
    publication_status: str
    display_order: int
    created_at: datetime
    updated_at: datetime
