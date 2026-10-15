"""CMS schema validation tests (no DB, no network)."""

import pytest
from pydantic import ValidationError

from app.models.cms_enums import PublicationStatus
from app.schemas.gallery import GalleryItemCreate, gallery_item_to_out
from app.schemas.portfolio import (
    PortfolioGalleryAttach,
    PortfolioProjectCreate,
    PortfolioProjectUpdate,
)
from app.schemas.uploaded_media import MediaRefOut, assert_allowed_image_extension


def test_portfolio_slug_normalized():
    payload = PortfolioProjectCreate(name="Lake Villa", slug="Lake-Villa")
    assert payload.slug == "lake-villa"
    assert payload.publication_status == PublicationStatus.DRAFT


def test_portfolio_slug_rejects_spaces():
    with pytest.raises(ValidationError):
        PortfolioProjectCreate(name="X", slug="bad slug")


def test_clear_main_image_conflict():
    with pytest.raises(ValidationError):
        PortfolioProjectUpdate(main_image_id=1, clear_main_image=True)


def test_gallery_attach_orders_must_match():
    with pytest.raises(ValidationError):
        PortfolioGalleryAttach(media_ids=[1, 2], display_orders=[0])


def test_gallery_object_position():
    item = GalleryItemCreate(media_id=3, object_position="Bottom Left")
    assert item.object_position == "bottom left"


def test_gallery_item_to_out_src_fields():
    class _Media:
        id = 9
        url_path = "/media/gallery/a.webp"
        mime_type = "image/webp"
        width = None
        height = None
        original_filename = "a.webp"

    class _Item:
        id = 1
        media_id = 9
        caption = "Hall"
        category = "interior"
        object_position = "center"
        display_order = 0
        publication_status = "PUBLISHED"
        notes = None
        media = _Media()
        created_at = "2026-01-01T00:00:00Z"
        updated_at = "2026-01-01T00:00:00Z"

    # Use real datetimes via MediaRef helper path with dict-like constructed Out
    from datetime import datetime, timezone

    _Item.created_at = datetime.now(timezone.utc)
    _Item.updated_at = datetime.now(timezone.utc)

    out = gallery_item_to_out(_Item(), public_base_url="https://cdn.example.test")
    assert out.src == "/media/gallery/a.webp"
    assert out.src_full == "https://cdn.example.test/media/gallery/a.webp"
    assert isinstance(out.media, MediaRefOut)


def test_svg_extension_helper_rejected():
    with pytest.raises(ValueError):
        assert_allowed_image_extension("svg")
