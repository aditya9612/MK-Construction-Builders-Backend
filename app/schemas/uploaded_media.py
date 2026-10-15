"""Pydantic schemas for website CMS uploaded media."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.cms_enums import MediaFolder
from app.schemas.common import ORMModel

ALLOWED_IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})
ALLOWED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


class UploadedMediaOut(ORMModel):
    id: int
    folder: str
    original_filename: str
    stored_filename: str
    storage_key: str
    url_path: str
    mime_type: str
    extension: str
    size_bytes: int
    width: int | None
    height: int | None
    created_at: datetime
    updated_at: datetime


class MediaUploadMeta(BaseModel):
    """Optional metadata supplied with multipart uploads (Phase 4)."""

    folder: MediaFolder = MediaFolder.GALLERY
    alt_text: str | None = Field(default=None, max_length=255)


class MediaRefOut(ORMModel):
    """Compact media reference for nested portfolio/gallery responses."""

    id: int
    url_path: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    original_filename: str | None = None


def normalize_extension(value: str) -> str:
    ext = value.lower().lstrip(".")
    if ext == "jpeg":
        return "jpg"
    return ext


def assert_allowed_image_extension(extension: str) -> str:
    ext = normalize_extension(extension)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(
            f"Unsupported image extension '{extension}'. Allowed: jpeg, png, webp"
        )
    return ext


def assert_allowed_image_mime(mime_type: str) -> str:
    normalized = mime_type.lower().strip()
    if normalized not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError(
            f"Unsupported MIME type '{mime_type}'. Allowed: image/jpeg, image/png, image/webp"
        )
    return normalized


class ImageValidationHints(BaseModel):
    """Shared validation constraints for upload services (Phase 4).

    Full content/dimension validation requires Pillow, which is not yet approved.
    """

    max_file_size_bytes: int = Field(default=5 * 1024 * 1024, ge=1)
    max_batch_size: int = Field(default=20, ge=1, le=50)
    max_width: int = Field(default=8000, ge=1)
    max_height: int = Field(default=8000, ge=1)
    min_width: int = Field(default=1, ge=1)
    min_height: int = Field(default=1, ge=1)
    allowed_folders: list[MediaFolder] = Field(default_factory=lambda: list(MediaFolder))

    @field_validator("allowed_folders")
    @classmethod
    def folders_not_empty(cls, value: list[MediaFolder]) -> list[MediaFolder]:
        if not value:
            raise ValueError("At least one media folder must be allowed")
        return value
