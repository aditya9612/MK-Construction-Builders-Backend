"""Unit tests verifying Phase 5.1 fixes for CMS verified issues (C-1 through L-2)."""

import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, UploadFile
from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from app.api.routes import portfolio as portfolio_routes
from app.core.exceptions import ConflictError, ValidationFailedError
from app.core.media_settings import MediaSettings
from app.models.cms_enums import (
    GalleryCategory,
    MediaFolder,
    PortfolioDisplayStatus,
    PortfolioProjectType,
    PublicationStatus,
)
from app.models.gallery_item import GalleryItem
from app.models.portfolio_gallery import PortfolioProjectGallery
from app.models.portfolio_project import PortfolioProject
from app.models.uploaded_media import UploadedMedia
from app.repositories.gallery_repository import (
    ALLOWED_GALLERY_SORT_FIELDS,
    GalleryRepository,
)
from app.repositories.media_repository import (
    ALLOWED_MEDIA_SORT_FIELDS,
    MediaRepository,
)
from app.repositories.portfolio_repository import (
    ALLOWED_PORTFOLIO_SORT_FIELDS,
    PortfolioRepository,
)
from app.schemas.portfolio import PortfolioGalleryAttach
from app.services.portfolio_service import PortfolioService, _to_out

from app.services.upload_service import UploadService
from app.utils.image_sniff import validate_upload_identity

JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 20


class _DummySession:
    def __init__(self):
        self.add = MagicMock()
        self.flush = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock()
        self.execute = AsyncMock()


# --- C-1: Safe Relationship Initialization ---
def test_c1_mapper_configuration_succeeds_in_isolation():
    """Verify configure_mappers() does not raise InvalidRequestError or KeyError."""
    configure_mappers()
    assert PortfolioProject.__mapper__ is not None
    assert UploadedMedia.__mapper__ is not None
    assert PortfolioProjectGallery.__mapper__ is not None
    assert GalleryItem.__mapper__ is not None


# --- H-1: Commit Rollback & Storage Cleanup ---
@pytest.mark.asyncio
async def test_h1_upload_image_cleans_up_on_commit_failure():
    session = _DummySession()
    session.commit.side_effect = RuntimeError("DB connection dropped")
    mock_storage = MagicMock()
    mock_storage.build_storage_key.return_value = (
        "gallery/test.jpg",
        "test.jpg",
        "/media/gallery/test.jpg",
    )
    mock_storage.ensure_root.return_value = None
    mock_storage.save_bytes = AsyncMock(return_value=Path("/tmp/test.jpg"))
    mock_storage.delete_by_storage_key = AsyncMock()

    service = UploadService(session, storage=mock_storage)
    file = UploadFile(
        filename="site.jpg",
        file=io.BytesIO(JPEG_HEADER + b"data"),
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(RuntimeError, match="DB connection dropped"):
        await service.upload_image(file)

    session.rollback.assert_awaited_once()
    mock_storage.delete_by_storage_key.assert_awaited_once_with("gallery/test.jpg")


# --- H-2: Bounded Chunked Reads ---
@pytest.mark.asyncio
async def test_h2_oversized_file_rejected_without_full_read():
    session = _DummySession()
    mock_storage = MagicMock()
    settings = MediaSettings(
        media_root=Path("/tmp"),
        url_prefix="/media",
        public_base_url=None,
        max_file_size_bytes=100,
        max_batch_size=5,
    )
    service = UploadService(session, storage=mock_storage)
    service.media_settings = settings

    # 500 bytes of data (exceeds max_file_size_bytes=100)
    oversized_data = JPEG_HEADER + b"x" * 500
    file = UploadFile(
        filename="large.jpg",
        file=io.BytesIO(oversized_data),
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(ValidationFailedError, match="File exceeds maximum size of 100 bytes"):
        await service._store_one(file, folder=MediaFolder.GALLERY)



# --- H-3: Validate sort_by against Per-Model Allowlists ---
def test_h3_sort_by_allowlists_and_safe_fallback():
    session = _DummySession()

    portfolio_repo = PortfolioRepository(session)  # type: ignore[arg-type]
    # Invalid sort_by attribute that would otherwise crash getattr or .asc()
    stmt_portfolio = portfolio_repo.list_query(sort_by="__tablename__")
    compiled_p = str(stmt_portfolio.compile())
    # Should fall back to display_order
    assert "display_order" in compiled_p

    gallery_repo = GalleryRepository(session)  # type: ignore[arg-type]
    stmt_gallery = gallery_repo.list_query(sort_by="media")
    compiled_g = str(stmt_gallery.compile())
    assert "display_order" in compiled_g

    media_repo = MediaRepository(session)  # type: ignore[arg-type]
    stmt_media = media_repo.list_query(sort_by="portfolio_as_main")
    compiled_m = str(stmt_media.compile())
    assert "created_at" in compiled_m

    assert "display_order" in ALLOWED_PORTFOLIO_SORT_FIELDS
    assert "display_order" in ALLOWED_GALLERY_SORT_FIELDS
    assert "created_at" in ALLOWED_MEDIA_SORT_FIELDS


# --- H-4: IntegrityError Handled Across Entire attach_gallery Transaction ---
@pytest.mark.asyncio
async def test_h4_attach_gallery_handles_flush_integrity_error():
    session = _DummySession()
    service = PortfolioService(session)

    project = PortfolioProject(
        id=1,
        name="P1",
        slug="p1",
        type="RESIDENTIAL",
        status="COMPLETED",
        publication_status="PUBLISHED",
    )
    service.repo.get = AsyncMock(return_value=project)
    service.media_repo.get_many = AsyncMock(return_value=[MagicMock(id=10)])
    service.repo.max_gallery_order = AsyncMock(return_value=0)
    service.repo.get_gallery_link = AsyncMock(return_value=None)
    # Simulate IntegrityError during flush
    service.repo.add_gallery_link = AsyncMock(
        side_effect=IntegrityError("INSERT", {}, Exception("Duplicate key"))
    )

    payload = PortfolioGalleryAttach(media_ids=[10])
    with pytest.raises(ConflictError, match="Gallery attachment conflict"):
        await service.attach_gallery(1, payload)

    session.rollback.assert_awaited_once()


# --- M-1: Foreign Key ondelete RESTRICT on main_image_id ---
def test_m1_main_image_id_fk_ondelete_is_restrict():
    col = PortfolioProject.__table__.c.main_image_id
    fk = list(col.foreign_keys)[0]
    assert fk.ondelete == "RESTRICT"


# --- M-2: Compatible Gallery Detach Endpoints ---
def test_m2_gallery_detach_endpoints_exist_and_require_auth():
    app = FastAPI()
    for router in portfolio_routes.routers:
        app.include_router(router, prefix="/api/v1")

    paths = set(app.openapi()["paths"].keys())
    # Both new alternatives exist alongside original
    assert "/api/v1/admin/portfolio/projects/{project_id}/gallery/{media_id}" in paths
    assert "/api/v1/admin/portfolio/projects/{project_id}/gallery/detach" in paths
    assert "/api/v1/admin/portfolio/projects/{project_id}/gallery" in paths

    # Verify require_masters dependency on the new routes
    for route in portfolio_routes.admin_router.routes:
        if isinstance(route, APIRoute) and (
            "{media_id}" in route.path or "detach" in route.path
        ):
            dep_names = {
                getattr(dep.call, "__name__", "")
                for dep in route.dependant.dependencies
            }
            assert "require_masters" in dep_names


# --- M-3: Query Parameter Enum Validation ---
def test_m3_query_parameters_use_enums():
    # Check portfolio routes
    for route in portfolio_routes.public_router.routes:
        if isinstance(route, APIRoute) and route.path == "/portfolio/projects" and "GET" in route.methods:
            param_types = {
                (param.field_info.alias or param.name): param.field_info.annotation
                for param in route.dependant.query_params
            }
            assert param_types.get("type") == (PortfolioProjectType | None)
            assert param_types.get("status") == (PortfolioDisplayStatus | None)

    for route in portfolio_routes.admin_router.routes:
        if isinstance(route, APIRoute) and route.path == "/admin/portfolio/projects" and "GET" in route.methods:
            param_types = {
                (param.field_info.alias or param.name): param.field_info.annotation
                for param in route.dependant.query_params
            }
            assert param_types.get("type") == (PortfolioProjectType | None)
            assert param_types.get("status") == (PortfolioDisplayStatus | None)
            assert param_types.get("publication_status") == (PublicationStatus | None)



# --- L-1: Basename Extraction without Weakening Path Traversal Protection ---
def test_l1_filename_basename_and_traversal_protection():
    # Valid Windows path with directories
    ext, mime = validate_upload_identity(
        filename=r"C:\Users\Admin\Pictures\photo.jpg",
        declared_content_type="image/jpeg",
        header=JPEG_HEADER,
    )
    assert ext == "jpg"
    assert mime == "image/jpeg"

    # Valid Unix path
    ext, mime = validate_upload_identity(
        filename="uploads/sub/image.jpg",
        declared_content_type="image/jpeg",
        header=JPEG_HEADER,
    )
    assert ext == "jpg"

    # Path traversal with '..' must be rejected
    with pytest.raises(ValueError, match="Invalid upload filename"):
        validate_upload_identity(
            filename="../etc/passwd.jpg",
            declared_content_type="image/jpeg",
            header=JPEG_HEADER,
        )


# --- L-2: Deterministic Secondary Gallery Ordering ---
def test_l2_deterministic_secondary_gallery_ordering():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    # Model relationship order_by includes display_order and id
    rel = PortfolioProject.__mapper__.relationships["gallery_links"]
    order_cols = [str(c) for c in rel.order_by]
    assert any("display_order" in c for c in order_cols)
    assert any("id" in c for c in order_cols)

    # _to_out tiebreaker
    link1 = SimpleNamespace(id=20, media_id=1, display_order=1, media=None)
    link2 = SimpleNamespace(id=10, media_id=2, display_order=1, media=None)
    now = datetime.now(timezone.utc)
    proj = SimpleNamespace(
        id=1,
        name="Project One",
        slug="project-one",
        location=None,
        type="RESIDENTIAL",
        status="COMPLETED",
        main_image_id=None,
        main_image=None,
        description=None,
        overview=None,
        work_progress=None,
        final_result=None,
        publication_status="PUBLISHED",
        display_order=0,
        gallery_links=[link1, link2],
        created_at=now,
        updated_at=now,
    )
    out = _to_out(proj)
    # Link with id=10 must precede link with id=20 when display_order is equal (1)
    assert out.gallery[0].id == 10
    assert out.gallery[1].id == 20

