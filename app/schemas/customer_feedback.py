"""Pydantic schemas for customer feedback and Google reviews."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.customer_feedback import ReviewSource
from app.schemas.common import ORMModel

URL_REGEX = re.compile(
    r"^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;%=]+$",
    re.IGNORECASE,
)


def _validate_clean_string(value: str | None, field_name: str, min_length: int = 1) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if len(cleaned) < min_length:
        raise ValueError(f"{field_name} must not be empty or whitespace only")
    return cleaned


def _validate_google_url(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if not URL_REGEX.match(cleaned):
        raise ValueError("google_review_url must be a valid HTTP or HTTPS URL")
    return cleaned


class CustomerFeedbackCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=150, description="Customer name")
    customer_location: str = Field(
        ..., min_length=1, max_length=150, description="Customer city/location"
    )
    customer_photo: str | None = Field(
        default=None, max_length=500, description="Customer profile photo URL or path"
    )
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    review_title: str | None = Field(default=None, max_length=200, description="Review heading")
    review_message: str = Field(
        ..., min_length=1, description="Customer feedback / review message"
    )
    project_name: str | None = Field(
        default=None, max_length=200, description="Related construction project"
    )
    review_source: ReviewSource = Field(
        default=ReviewSource.WEBSITE, description="Review source: google, website, manual"
    )
    google_review_url: str | None = Field(
        default=None, max_length=500, description="Original Google review URL"
    )
    review_date: date | None = Field(
        default=None, description="Original review date (defaults to today)"
    )
    is_featured: bool = Field(default=False, description="Featured review flag")
    is_published: bool = Field(default=False, description="Public visibility flag")
    display_order: int = Field(default=0, ge=0, description="Display sequence order")

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        res = _validate_clean_string(value, "Customer name")
        assert res is not None
        return res

    @field_validator("customer_location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        res = _validate_clean_string(value, "Customer location")
        assert res is not None
        return res

    @field_validator("review_message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        res = _validate_clean_string(value, "Review message")
        assert res is not None
        return res

    @field_validator("review_title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Review title")

    @field_validator("project_name")
    @classmethod
    def validate_project(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Project name")

    @field_validator("google_review_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return _validate_google_url(value)


class CustomerFeedbackUpdate(BaseModel):
    customer_name: str | None = Field(
        default=None, min_length=1, max_length=150, description="Customer name"
    )
    customer_location: str | None = Field(
        default=None, min_length=1, max_length=150, description="Customer city/location"
    )
    customer_photo: str | None = Field(
        default=None, max_length=500, description="Customer profile photo URL or path"
    )
    rating: int | None = Field(default=None, ge=1, le=5, description="Rating between 1 and 5")
    review_title: str | None = Field(default=None, max_length=200, description="Review heading")
    review_message: str | None = Field(
        default=None, min_length=1, description="Customer feedback / review message"
    )
    project_name: str | None = Field(
        default=None, max_length=200, description="Related construction project"
    )
    review_source: ReviewSource | None = Field(
        default=None, description="Review source: google, website, manual"
    )
    google_review_url: str | None = Field(
        default=None, max_length=500, description="Original Google review URL"
    )
    review_date: date | None = Field(default=None, description="Original review date")
    is_featured: bool | None = Field(default=None, description="Featured review flag")
    is_published: bool | None = Field(default=None, description="Public visibility flag")
    display_order: int | None = Field(default=None, ge=0, description="Display sequence order")

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Customer name")

    @field_validator("customer_location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Customer location")

    @field_validator("review_message")
    @classmethod
    def validate_message(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Review message")

    @field_validator("review_title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Review title")

    @field_validator("project_name")
    @classmethod
    def validate_project(cls, value: str | None) -> str | None:
        return _validate_clean_string(value, "Project name")

    @field_validator("google_review_url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return _validate_google_url(value)


class CustomerFeedbackPublicResponse(ORMModel):
    """Public-safe customer feedback view (no internal administrative metadata)."""

    id: int
    customer_name: str
    customer_location: str
    customer_photo: str | None = None
    rating: int
    review_title: str | None = None
    review_message: str
    project_name: str | None = None
    review_source: str
    google_review_url: str | None = None
    review_date: date
    is_featured: bool
    display_order: int


class CustomerFeedbackResponse(ORMModel):
    """Full customer feedback view including audit timestamps and publication status."""

    id: int
    customer_name: str
    customer_location: str
    customer_photo: str | None = None
    rating: int
    review_title: str | None = None
    review_message: str
    project_name: str | None = None
    review_source: str
    google_review_url: str | None = None
    review_date: date
    is_featured: bool
    is_published: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class CustomerFeedbackListResponse(BaseModel):
    items: list[CustomerFeedbackResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CustomerFeedbackPublicStatisticsResponse(BaseModel):
    total_published_reviews: int
    average_rating: float
    rating_distribution: dict[str, int]
    total_google_reviews: int
    total_website_reviews: int


class CustomerFeedbackAdminStatisticsResponse(BaseModel):
    total_reviews: int
    published_reviews: int
    pending_reviews: int
    featured_reviews: int
    average_rating: float
    google_review_count: int
    website_review_count: int
    manual_review_count: int = 0
    rating_distribution: dict[str, int] = Field(default_factory=dict)


class CustomerReviewPublicSubmit(BaseModel):
    """Payload for public website review submissions.

    Server controls is_published (True), review_source ('website'),
    is_featured (False), and display_order (0). Extra fields are ignored.
    """

    model_config = ConfigDict(extra="ignore")

    customer_name: str = Field(..., min_length=1, max_length=150, description="Customer name")
    customer_location: str = Field(
        ..., min_length=1, max_length=150, description="Customer city/location"
    )
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    review_message: str = Field(
        ..., min_length=1, description="Customer feedback / review message"
    )
    review_title: str | None = Field(default=None, max_length=200, description="Review heading")
    customer_photo: str | None = Field(
        default=None, max_length=500, description="Customer profile photo path"
    )
    honeypot: str | None = Field(
        default=None, max_length=100, description="Anti-spam honeypot (leave empty)"
    )

    @field_validator("customer_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        res = _validate_clean_string(value, "Customer name")
        assert res is not None
        if len(res) > 150:
            raise ValueError("Customer name must not exceed 150 characters")
        if re.search(r"<[^>]*>", res):
            raise ValueError("Customer name contains invalid characters or HTML")
        if re.search(r"https?://", res, re.IGNORECASE):
            raise ValueError("Customer name must not contain URLs")
        return res

    @field_validator("customer_location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        res = _validate_clean_string(value, "Customer location")
        assert res is not None
        if len(res) > 150:
            raise ValueError("Customer location must not exceed 150 characters")
        if re.search(r"<[^>]*>", res):
            raise ValueError("Customer location contains invalid characters or HTML")
        if re.search(r"https?://", res, re.IGNORECASE):
            raise ValueError("Customer location must not contain URLs")
        return res

    @field_validator("rating", mode="before")
    @classmethod
    def validate_rating(cls, value: Any) -> int:
        if isinstance(value, bool):
            raise ValueError("Rating must be an integer between 1 and 5")
        try:
            if isinstance(value, float):
                if not value.is_integer():
                    raise ValueError("Rating must be an integer between 1 and 5")
                value = int(value)
            elif isinstance(value, str):
                cleaned_str = value.strip()
                if not cleaned_str or "." in cleaned_str:
                    raise ValueError("Rating must be an integer between 1 and 5")
                value = int(cleaned_str)
            elif not isinstance(value, int):
                raise ValueError("Rating must be an integer between 1 and 5")
        except (ValueError, TypeError):
            raise ValueError("Rating must be an integer between 1 and 5")

        if value < 1 or value > 5:
            raise ValueError("Rating must be an integer between 1 and 5")
        return value

    @field_validator("review_message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        res = _validate_clean_string(value, "Review message")
        assert res is not None
        if re.search(r"<script[^>]*>", res, re.IGNORECASE):
            raise ValueError("Review message contains invalid script tags")
        links = re.findall(r"https?://", res, re.IGNORECASE)
        if len(links) > 2:
            raise ValueError("Review message contains too many links")
        return res

    @field_validator("review_title", mode="before")
    @classmethod
    def validate_title(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            if len(cleaned) > 200:
                raise ValueError("Review title must not exceed 200 characters")
            if re.search(r"<[^>]*>", cleaned):
                raise ValueError("Review title contains invalid characters or HTML")
            return cleaned
        return value

    @field_validator("customer_photo")
    @classmethod
    def validate_photo_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if "\\" in cleaned or ".." in cleaned or cleaned.startswith(("file:", "C:", "c:")):
            raise ValueError("Invalid customer photo path")
        return cleaned

    @field_validator("honeypot")
    @classmethod
    def validate_honeypot(cls, value: str | None) -> str | None:
        if value and value.strip():
            raise ValueError("Spam detected: honeypot field must be empty")
        return None


class FeedbackPublishUpdate(BaseModel):
    is_published: bool = Field(..., description="Publication status")


class FeedbackFeaturedUpdate(BaseModel):
    is_featured: bool = Field(..., description="Featured status")


class FeedbackDisplayOrderUpdate(BaseModel):
    display_order: int = Field(..., ge=0, description="Display sequence order")


class PhotoUploadResponse(BaseModel):
    url_path: str
    stored_filename: str
