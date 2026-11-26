"""Pydantic v2 schemas and Instagram URL validation for Instagram Reels management."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import ORMModel

ALLOWED_INSTAGRAM_DOMAINS = frozenset(
    {"instagram.com", "www.instagram.com", "m.instagram.com"}
)
_PATH_REGEX = re.compile(r"^/(reel|reels|p)/([^/]+)/?\Z", re.IGNORECASE)
_SHORTCODE_REGEX = re.compile(r"^(?=.*[A-Za-z0-9])[A-Za-z0-9_-]{4,64}\Z")


def parse_and_normalize_instagram_url(raw_url: str) -> tuple[str, str, str]:
    """Validate an Instagram Reel/Post URL and normalize it to canonical HTTPS + embed URLs.

    Note:
        Syntactic validation and canonicalization only verify that the URL is a
        well-formed HTTPS Instagram reel/post URL; they do not guarantee that the
        target Instagram Reel exists or is publicly embeddable by Instagram.

    Returns:
        (canonical_instagram_url, embed_url, shortcode)
    """
    if not isinstance(raw_url, str):
        raise ValueError("instagram_url must be a string")

    cleaned = raw_url.strip()
    if not cleaned:
        raise ValueError("instagram_url must not be empty")
    if len(cleaned) > 500:
        raise ValueError("instagram_url must not exceed 500 characters")
    if any(ch.isspace() or ord(ch) < 32 for ch in cleaned) or "\\" in cleaned:
        raise ValueError("instagram_url contains invalid characters")

    try:
        parsed = urlsplit(cleaned)
    except ValueError as exc:
        raise ValueError("instagram_url is malformed") from exc

    if parsed.scheme.lower() != "https":
        raise ValueError("instagram_url must use the https scheme")

    if parsed.username is not None or parsed.password is not None or "@" in parsed.netloc:
        raise ValueError("instagram_url must not contain embedded credentials")

    netloc = parsed.netloc.lower()
    host = (parsed.hostname or "").lower()
    if netloc not in ALLOWED_INSTAGRAM_DOMAINS or host not in ALLOWED_INSTAGRAM_DOMAINS:
        raise ValueError(
            "instagram_url must use instagram.com, www.instagram.com, or m.instagram.com"
        )

    match = _PATH_REGEX.fullmatch(parsed.path or "")
    if not match:
        raise ValueError(
            "instagram_url path must be /reel/{shortcode}/, /reels/{shortcode}/, or /p/{shortcode}/"
        )

    kind = match.group(1).lower()
    shortcode = match.group(2)
    if not _SHORTCODE_REGEX.fullmatch(shortcode):
        raise ValueError("instagram_url contains an invalid shortcode")

    canonical_kind = "p" if kind == "p" else "reel"
    canonical_url = f"https://www.instagram.com/{canonical_kind}/{shortcode}/"
    embed_url = f"https://www.instagram.com/{canonical_kind}/{shortcode}/embed/"

    if len(canonical_url) > 500 or len(embed_url) > 500:
        raise ValueError("Normalized Instagram URL exceeds maximum length of 500 characters")

    return canonical_url, embed_url, shortcode


def _normalize_title(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("title must not be empty or whitespace only")
    if len(cleaned) > 200:
        raise ValueError("title must not exceed 200 characters")
    return cleaned


def _normalize_description(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _reject_bool_for_int(value: Any) -> Any:
    if isinstance(value, bool):
        raise ValueError("display_order must be a non-negative integer")
    return value


class InstagramReelCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    instagram_url: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    is_published: bool = Field(default=False)
    display_order: int = Field(default=0, ge=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return _normalize_title(value)

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram_url(cls, value: str) -> str:
        canonical_url, _, _ = parse_and_normalize_instagram_url(value)
        return canonical_url

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return _normalize_description(value)

    @field_validator("display_order", mode="before")
    @classmethod
    def validate_display_order_type(cls, value: Any) -> Any:
        return _reject_bool_for_int(value)


class InstagramReelUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    instagram_url: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    is_published: bool | None = Field(default=None)
    display_order: int | None = Field(default=None, ge=0)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _normalize_title(value)

    @field_validator("instagram_url")
    @classmethod
    def validate_instagram_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        canonical_url, _, _ = parse_and_normalize_instagram_url(value)
        return canonical_url

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        return _normalize_description(value)

    @field_validator("display_order", mode="before")
    @classmethod
    def validate_display_order_type(cls, value: Any) -> Any:
        return _reject_bool_for_int(value)

    @model_validator(mode="after")
    def validate_non_empty_and_non_null_fields(self) -> "InstagramReelUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        for field_name in ("title", "instagram_url", "is_published", "display_order"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class InstagramReelPublishUpdate(BaseModel):
    is_published: bool = Field(...)


class InstagramReelOrderUpdate(BaseModel):
    display_order: int = Field(..., ge=0)

    @field_validator("display_order", mode="before")
    @classmethod
    def validate_display_order_type(cls, value: Any) -> Any:
        return _reject_bool_for_int(value)


class InstagramReelOut(ORMModel):
    id: int
    title: str
    instagram_url: str
    embed_url: str
    description: str | None = None
    is_published: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class InstagramReelPublicOut(ORMModel):
    id: int
    title: str
    instagram_url: str
    embed_url: str
    description: str | None = None
    display_order: int


class InstagramReelPublicListOut(BaseModel):
    is_enabled: bool
    items: list[InstagramReelPublicOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class InstagramSectionSettingsUpdate(BaseModel):
    is_enabled: bool = Field(...)


class InstagramSectionSettingsOut(ORMModel):
    id: int
    is_enabled: bool
    updated_at: datetime
