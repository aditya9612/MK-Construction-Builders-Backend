"""Pydantic schemas for website gallery items."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.cms_enums import GalleryCategory, PublicationStatus
from app.schemas.common import ORMModel
from app.schemas.uploaded_media import MediaRefOut

OBJECT_POSITION_PATTERN = (
    "center",
    "top",
    "bottom",
    "left",
    "right",
    "top left",
    "top right",
    "bottom left",
    "bottom right",
)


class GalleryItemCreate(BaseModel):
    media_id: int = Field(ge=1)
    caption: str | None = Field(default=None, max_length=500)
    category: GalleryCategory = GalleryCategory.OTHER
    object_position: str = Field(default="center", max_length=50)
    display_order: int = Field(default=0, ge=0)
    publication_status: PublicationStatus = PublicationStatus.DRAFT
    notes: str | None = None

    @field_validator("object_position")
    @classmethod
    def object_position_ok(cls, value: str) -> str:
        normalized = " ".join(value.strip().lower().split())
        if normalized not in OBJECT_POSITION_PATTERN:
            raise ValueError(
                "object_position must be one of: "
                + ", ".join(OBJECT_POSITION_PATTERN)
            )
        return normalized


class GalleryItemUpdate(BaseModel):
    media_id: int | None = Field(default=None, ge=1)
    caption: str | None = Field(default=None, max_length=500)
    category: GalleryCategory | None = None
    object_position: str | None = Field(default=None, max_length=50)
    display_order: int | None = Field(default=None, ge=0)
    publication_status: PublicationStatus | None = None
    notes: str | None = None

    @field_validator("object_position")
    @classmethod
    def object_position_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = " ".join(value.strip().lower().split())
        if normalized not in OBJECT_POSITION_PATTERN:
            raise ValueError(
                "object_position must be one of: "
                + ", ".join(OBJECT_POSITION_PATTERN)
            )
        return normalized


class GalleryItemOut(ORMModel):
    """Gallery item with media refs and src/src_full compatibility fields."""

    id: int
    media_id: int
    caption: str | None
    category: str
    object_position: str
    display_order: int
    publication_status: str
    notes: str | None = None
    media: MediaRefOut | None = None
    src: str | None = None
    src_full: str | None = None
    created_at: datetime
    updated_at: datetime


def gallery_item_to_out(
    item: object,
    *,
    media: MediaRefOut | None = None,
    public_base_url: str | None = None,
) -> GalleryItemOut:
    """Build GalleryItemOut with src / src_full compatibility.

    ``public_base_url`` is optional; when set, src_full becomes an absolute URL.
    Domains must come from configuration — never hardcode them.
    """
    media_ref = media
    if media_ref is None and getattr(item, "media", None) is not None:
        m = item.media
        media_ref = MediaRefOut(
            id=m.id,
            url_path=m.url_path,
            mime_type=m.mime_type,
            width=m.width,
            height=m.height,
            original_filename=m.original_filename,
        )

    url_path = media_ref.url_path if media_ref else None
    src_full = url_path
    if public_base_url and url_path:
        base = public_base_url.rstrip("/")
        path = url_path if url_path.startswith("/") else f"/{url_path}"
        src_full = f"{base}{path}"

    return GalleryItemOut(
        id=item.id,
        media_id=item.media_id,
        caption=item.caption,
        category=item.category,
        object_position=item.object_position,
        display_order=item.display_order,
        publication_status=item.publication_status,
        notes=getattr(item, "notes", None),
        media=media_ref,
        src=url_path,
        src_full=src_full,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
