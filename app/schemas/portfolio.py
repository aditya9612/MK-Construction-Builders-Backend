"""Pydantic schemas for website portfolio projects (not ERP projects)."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.cms_enums import (
    PortfolioDisplayStatus,
    PortfolioProjectType,
    PublicationStatus,
)
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


class PortfolioGalleryImageOut(ORMModel):
    id: int
    media_id: int
    display_order: int
    media: MediaRefOut | None = None


class PortfolioProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=220)
    location: str | None = Field(default=None, max_length=200)
    type: PortfolioProjectType = PortfolioProjectType.RESIDENTIAL
    status: PortfolioDisplayStatus = PortfolioDisplayStatus.COMPLETED
    main_image_id: int | None = Field(default=None, ge=1)
    description: str | None = None
    overview: str | None = None
    work_progress: str | None = None
    final_result: str | None = None
    publication_status: PublicationStatus = PublicationStatus.DRAFT
    display_order: int = Field(default=0, ge=0)
    gallery_media_ids: list[int] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_ok(cls, value: str) -> str:
        return _normalize_slug(value)

    @field_validator("gallery_media_ids")
    @classmethod
    def gallery_ids_unique(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("gallery_media_ids must contain positive integers")
        if len(value) != len(set(value)):
            raise ValueError("gallery_media_ids must not contain duplicates")
        return value


class PortfolioProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, min_length=1, max_length=220)
    location: str | None = Field(default=None, max_length=200)
    type: PortfolioProjectType | None = None
    status: PortfolioDisplayStatus | None = None
    main_image_id: int | None = Field(default=None, ge=1)
    clear_main_image: bool = False
    description: str | None = None
    overview: str | None = None
    work_progress: str | None = None
    final_result: str | None = None
    publication_status: PublicationStatus | None = None
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("slug")
    @classmethod
    def slug_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _normalize_slug(value)

    @model_validator(mode="after")
    def main_image_rules(self) -> "PortfolioProjectUpdate":
        if self.clear_main_image and self.main_image_id is not None:
            raise ValueError("Cannot set main_image_id and clear_main_image together")
        return self


class PortfolioGalleryAttach(BaseModel):
    """Attach one or more media items to a portfolio project's gallery."""

    media_ids: list[int] = Field(min_length=1)
    display_orders: list[int] | None = None

    @field_validator("media_ids")
    @classmethod
    def media_ids_ok(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("media_ids must contain positive integers")
        if len(value) != len(set(value)):
            raise ValueError("media_ids must not contain duplicates")
        return value

    @model_validator(mode="after")
    def orders_match(self) -> "PortfolioGalleryAttach":
        if self.display_orders is not None and len(self.display_orders) != len(self.media_ids):
            raise ValueError("display_orders length must match media_ids length")
        if self.display_orders is not None and any(order < 0 for order in self.display_orders):
            raise ValueError("display_orders must be >= 0")
        return self


class PortfolioGalleryDetach(BaseModel):
    """Detach media items from a portfolio project's gallery by media id."""

    media_ids: list[int] = Field(min_length=1)

    @field_validator("media_ids")
    @classmethod
    def media_ids_ok(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("media_ids must contain positive integers")
        if len(value) != len(set(value)):
            raise ValueError("media_ids must not contain duplicates")
        return value


class PortfolioProjectOut(ORMModel):
    id: int
    name: str
    slug: str
    location: str | None
    type: str
    status: str
    main_image_id: int | None
    main_image: MediaRefOut | None = None
    description: str | None
    overview: str | None
    work_progress: str | None
    final_result: str | None
    publication_status: str
    display_order: int
    gallery: list[PortfolioGalleryImageOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PortfolioProjectListItemOut(ORMModel):
    """Lighter list payload for public/admin listing."""

    id: int
    name: str
    slug: str
    location: str | None
    type: str
    status: str
    main_image: MediaRefOut | None = None
    publication_status: str
    display_order: int
    created_at: datetime
    updated_at: datetime
