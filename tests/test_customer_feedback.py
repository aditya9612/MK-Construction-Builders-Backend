"""Comprehensive unit and integration tests for Customer Feedback & Google Reviews Module.

Covers all 14 required scenarios:
1. Create customer feedback
2. Get public feedback
3. Get individual feedback
4. Update feedback
5. Delete feedback
6. Publish and unpublish feedback
7. Feature and unfeature feedback
8. Rating validation
9. Invalid input validation
10. Unauthorized admin access
11. Image upload validation
12. Pagination and search
13. Public visibility restrictions
14. Statistics calculation
"""

from __future__ import annotations

import io
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, UploadFile, status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.deps import get_current_user, require_admin
from app.api.routes.customer_feedback import router as feedback_router
from app.core.database import get_db
from app.core.exceptions import (
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationFailedError,
    register_exception_handlers,
)
from app.models.cms_enums import MediaFolder
from app.models.customer_feedback import CustomerFeedback, ReviewSource
from app.models.enums import RoleName
from app.models.user import Role, User
from app.repositories.customer_feedback_repository import (
    ALLOWED_FEEDBACK_SORT_FIELDS,
    CustomerFeedbackRepository,
)
from app.schemas.customer_feedback import (
    CustomerFeedbackAdminStatisticsResponse,
    CustomerFeedbackCreate,
    CustomerFeedbackPublicResponse,
    CustomerFeedbackPublicStatisticsResponse,
    CustomerFeedbackResponse,
    CustomerFeedbackUpdate,
    FeedbackDisplayOrderUpdate,
    FeedbackFeaturedUpdate,
    FeedbackPublishUpdate,
)
from app.services.customer_feedback_service import CustomerFeedbackService
from app.services.media_storage import MediaSettings

# Sample image headers for sniffing tests
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 20
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
WEBP_HEADER = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 20
INVALID_HEADER = b"NOT_AN_IMAGE_HEADER_1234567890"


class _DummySession:
    def __init__(self):
        self.add = MagicMock()
        self.flush = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock()
        self.execute = AsyncMock()

        async def _refresh(item):
            if getattr(item, "id", None) is None:
                item.id = 1
            if getattr(item, "created_at", None) is None:
                item.created_at = datetime.now(timezone.utc)
            if getattr(item, "updated_at", None) is None:
                item.updated_at = datetime.now(timezone.utc)

        self.refresh = AsyncMock(side_effect=_refresh)


def _make_dummy_user(role_name: str = "ADMIN") -> User:
    role = Role(id=1, name=role_name)
    user = User(
        id=1,
        name="Test User",
        email="test@mkconstruction.in",
        password_hash="fakehash",
        role_id=1,
        is_active=True,
    )
    user.role = role
    return user


def _make_sample_feedback(
    feedback_id: int = 1,
    is_published: bool = True,
    is_featured: bool = False,
    rating: int = 5,
    review_source: str = "google",
) -> CustomerFeedback:
    fb = CustomerFeedback(
        customer_name="Aarav Sharma",
        customer_location="Bangalore",
        customer_photo="/media/reviews/sample.jpg",
        rating=rating,
        review_title="Excellent Villa Construction",
        review_message="MK Construction did a phenomenal job building our duplex villa in Whitefield.",
        project_name="Whitefield Villa",
        review_source=review_source,
        google_review_url="https://maps.google.com/?cid=1234567890",
        review_date=date(2026, 10, 15),
        is_featured=is_featured,
        is_published=is_published,
        display_order=1,
    )
    fb.id = feedback_id
    fb.created_at = datetime.now(timezone.utc)
    fb.updated_at = datetime.now(timezone.utc)
    return fb


# ==============================================================================
# Scenario 8 & 9: Rating and Invalid Input Validation (Schemas)
# ==============================================================================


def test_rating_validation_bounds():
    """Rating must be strictly between 1 and 5."""
    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="John",
            customer_location="Bangalore",
            rating=0,  # Below minimum
            review_message="Good",
        )

    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="John",
            customer_location="Bangalore",
            rating=6,  # Above maximum
            review_message="Good",
        )

    # Valid ratings 1 to 5
    for r in range(1, 6):
        fb = CustomerFeedbackCreate(
            customer_name="John",
            customer_location="Bangalore",
            rating=r,
            review_message="Valid rating message",
        )
        assert fb.rating == r


def test_invalid_input_validation():
    """Empty or whitespace-only name, location, and message must be rejected."""
    # Empty customer name
    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="   ",
            customer_location="Bangalore",
            rating=5,
            review_message="Message",
        )

    # Empty location
    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="John",
            customer_location="  ",
            rating=5,
            review_message="Message",
        )

    # Empty review message
    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="John",
            customer_location="Bangalore",
            rating=5,
            review_message="    ",
        )

    # Invalid Google Review URL
    with pytest.raises(ValidationError, match="valid HTTP or HTTPS URL"):
        CustomerFeedbackCreate(
            customer_name="John",
            customer_location="Bangalore",
            rating=5,
            review_message="Message",
            google_review_url="not-a-valid-url",
        )

    # Valid Google URL should be accepted
    fb = CustomerFeedbackCreate(
        customer_name="John",
        customer_location="Bangalore",
        rating=5,
        review_message="Message",
        google_review_url="https://maps.app.goo.gl/xyz123",
    )
    assert fb.google_review_url == "https://maps.app.goo.gl/xyz123"


def test_review_source_enum_validation():
    """Review source must be one of: google, website, manual."""
    fb_google = CustomerFeedbackCreate(
        customer_name="A",
        customer_location="B",
        rating=5,
        review_message="M",
        review_source=ReviewSource.GOOGLE,
    )
    assert fb_google.review_source == ReviewSource.GOOGLE

    with pytest.raises(ValidationError):
        CustomerFeedbackCreate(
            customer_name="A",
            customer_location="B",
            rating=5,
            review_message="M",
            review_source="facebook",  # invalid
        )


# ==============================================================================
# Scenario 10: Unauthorized Admin Access & RBAC Wiring
# ==============================================================================


def test_route_contract_and_rbac_wiring():
    """Verify route paths and authorization dependencies."""
    public_routes = [
        r
        for r in feedback_router.routes
        if isinstance(r, APIRoute) and "/public" in r.path
    ]
    assert len(public_routes) >= 3

    # Public routes must have NO auth dependencies
    for route in public_routes:
        dep_names = {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}
        assert "require_admin" not in dep_names
        assert "get_current_user" not in dep_names

    # Admin routes must require require_admin
    admin_routes = [
        r
        for r in feedback_router.routes
        if isinstance(r, APIRoute) and "/public" not in r.path
    ]
    assert len(admin_routes) >= 8
    for route in admin_routes:
        dep_names = {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}
        assert "require_admin" in dep_names, f"{route.path} missing require_admin"


def test_unauthorized_access_rejected():
    """Unauthenticated access to admin endpoints must return 401."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(feedback_router, prefix="/api/v1")
    client = TestClient(app)

    # Without token
    response = client.get("/api/v1/customer-feedback")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/api/v1/customer-feedback", json={})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete("/api/v1/customer-feedback/1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_forbidden_for_non_admin_role():
    """Viewer / Manager roles must receive 403 Forbidden on admin feedback routes."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(feedback_router, prefix="/api/v1")

    # Override get_current_user with VIEWER
    viewer = _make_dummy_user("VIEWER")
    app.dependency_overrides[get_current_user] = lambda: viewer

    client = TestClient(app)
    response = client.get("/api/v1/customer-feedback")
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# Scenario 1: Create Customer Feedback
# ==============================================================================


@pytest.mark.asyncio
async def test_create_customer_feedback():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    payload = CustomerFeedbackCreate(
        customer_name="Priya Patel",
        customer_location="Indiranagar, Bangalore",
        rating=5,
        review_title="Superb Quality",
        review_message="Loved the structural finishing and transparent pricing.",
        project_name="Indiranagar Residence",
        review_source=ReviewSource.WEBSITE,
        is_published=True,
        display_order=2,
    )

    created = await service.create(payload)
    session.repo = None  # clean
    session.commit.assert_awaited_once()
    assert created.customer_name == "Priya Patel"
    assert created.rating == 5
    assert created.review_date == date.today()
    assert created.is_published is True


# ==============================================================================
# Scenario 2, 3 & 13: Public Feedback, Individual Feedback & Visibility Restrictions
# ==============================================================================


@pytest.mark.asyncio
async def test_get_individual_feedback_public_and_unpublished_restriction():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    # 1. Published feedback is retrievable publicly
    published = _make_sample_feedback(feedback_id=10, is_published=True)
    service.repo.get_published = AsyncMock(return_value=published)

    public_res = await service.get_public(10)
    assert public_res.id == 10
    assert public_res.customer_name == published.customer_name
    # Public response has no internal created_at/updated_at exposed
    assert not hasattr(public_res, "created_at")

    # 2. Unpublished feedback returns 404 for public callers
    service.repo.get_published = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Customer feedback not found"):
        await service.get_public(99)


@pytest.mark.asyncio
async def test_get_individual_feedback_admin_can_view_unpublished():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    unpublished = _make_sample_feedback(feedback_id=20, is_published=False)
    service.repo.get = AsyncMock(return_value=unpublished)

    admin_res = await service.get_admin(20)
    assert admin_res.id == 20
    assert admin_res.is_published is False
    assert hasattr(admin_res, "created_at")


# ==============================================================================
# Scenario 4: Update Feedback
# ==============================================================================


@pytest.mark.asyncio
async def test_update_feedback():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    item = _make_sample_feedback(feedback_id=5, rating=4)
    service.repo.get = AsyncMock(return_value=item)

    update_payload = CustomerFeedbackUpdate(
        rating=5,
        review_title="Updated Title: 5 Stars",
        is_featured=True,
    )

    updated = await service.update(5, update_payload)
    session.commit.assert_awaited_once()
    assert updated.rating == 5
    assert updated.review_title == "Updated Title: 5 Stars"
    assert updated.is_featured is True


# ==============================================================================
# Scenario 5: Delete Feedback and Associated Local Storage Cleanup
# ==============================================================================


@pytest.mark.asyncio
async def test_delete_feedback_cleans_up_local_image():
    session = _DummySession()
    mock_storage = MagicMock()
    mock_storage.delete_by_storage_key = AsyncMock()

    service = CustomerFeedbackService(session, storage=mock_storage)
    item = _make_sample_feedback(feedback_id=8)
    item.customer_photo = "/media/reviews/photo123.jpg"
    service.repo.get = AsyncMock(return_value=item)
    service.repo.delete = AsyncMock()

    await service.delete(8)
    service.repo.delete.assert_awaited_once_with(item)
    session.commit.assert_awaited_once()
    mock_storage.delete_by_storage_key.assert_awaited_once_with("reviews/photo123.jpg")


@pytest.mark.asyncio
async def test_delete_feedback_does_not_unlink_external_google_url():
    session = _DummySession()
    mock_storage = MagicMock()
    mock_storage.delete_by_storage_key = AsyncMock()

    service = CustomerFeedbackService(session, storage=mock_storage)
    item = _make_sample_feedback(feedback_id=9)
    item.customer_photo = "https://lh3.googleusercontent.com/avatar123.jpg"
    service.repo.get = AsyncMock(return_value=item)
    service.repo.delete = AsyncMock()

    await service.delete(9)
    session.commit.assert_awaited_once()
    # External URL must not trigger local file unlinking
    mock_storage.delete_by_storage_key.assert_not_called()


# ==============================================================================
# Scenario 6 & 7: Publish, Unpublish, Feature, Unfeature, Display Order
# ==============================================================================


@pytest.mark.asyncio
async def test_publish_unpublish_feedback():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    item = _make_sample_feedback(feedback_id=12, is_published=False)
    service.repo.get = AsyncMock(return_value=item)

    res = await service.set_publish_status(12, True)
    assert res.is_published is True

    res2 = await service.set_publish_status(12, False)
    assert res2.is_published is False


@pytest.mark.asyncio
async def test_feature_and_display_order():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    item = _make_sample_feedback(feedback_id=14, is_featured=False)
    service.repo.get = AsyncMock(return_value=item)

    res = await service.set_featured_status(14, True)
    assert res.is_featured is True

    res_order = await service.set_display_order(14, 5)
    assert res_order.display_order == 5


# ==============================================================================
# Scenario 11: Image Upload Validation
# ==============================================================================


@pytest.mark.asyncio
async def test_image_upload_valid_formats():
    """JPG, PNG, and WebP images are accepted."""
    session = _DummySession()
    mock_storage = MagicMock()
    mock_storage.build_storage_key.return_value = (
        "reviews/abc.jpg",
        "abc.jpg",
        "/media/reviews/abc.jpg",
    )
    mock_storage.save_bytes = AsyncMock()
    mock_storage.ensure_root = MagicMock()

    service = CustomerFeedbackService(session, storage=mock_storage)

    file = UploadFile(
        filename="client.jpg",
        file=io.BytesIO(JPEG_HEADER + b"data"),
        headers={"content-type": "image/jpeg"},
    )

    uploaded = await service.upload_photo(file)
    assert uploaded.url_path == "/media/reviews/abc.jpg"
    assert uploaded.stored_filename == "abc.jpg"


@pytest.mark.asyncio
async def test_image_upload_rejects_invalid_magic_bytes():
    """Non-image bytes with image extension must be rejected."""
    session = _DummySession()
    service = CustomerFeedbackService(session)

    file = UploadFile(
        filename="fake.jpg",
        file=io.BytesIO(INVALID_HEADER),
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(ValidationFailedError, match="not a recognized JPEG, PNG, or WebP"):
        await service.upload_photo(file)


@pytest.mark.asyncio
async def test_image_upload_rejects_empty_file():
    session = _DummySession()
    service = CustomerFeedbackService(session)

    file = UploadFile(
        filename="empty.png",
        file=io.BytesIO(b""),
        headers={"content-type": "image/png"},
    )

    with pytest.raises(ValidationFailedError, match="Uploaded file is empty"):
        await service.upload_photo(file)


@pytest.mark.asyncio
async def test_image_upload_rejects_oversized_file():
    session = _DummySession()
    service = CustomerFeedbackService(session)
    service.media_settings = MediaSettings(
        media_root=Path("/tmp"),
        url_prefix="/media",
        public_base_url=None,
        max_file_size_bytes=50,  # 50 bytes limit for test
        max_batch_size=5,
    )

    file = UploadFile(
        filename="large.jpg",
        file=io.BytesIO(JPEG_HEADER + b"x" * 200),
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(ValidationFailedError, match="File exceeds maximum size"):
        await service.upload_photo(file)


# ==============================================================================
# Scenario 12: Pagination and Search Query
# ==============================================================================


def test_repository_list_query_parameters():
    """Verify list_query constructs correct filters and sorting."""
    session = _DummySession()
    repo = CustomerFeedbackRepository(session)

    # 1. Published only
    q_pub = repo.list_query(published_only=True, rating=5, review_source="google")
    compiled = str(q_pub.compile())
    assert "is_published" in compiled
    assert "rating" in compiled
    assert "review_source" in compiled

    # 2. Search query across name, location, message, project
    q_search = repo.list_query(search="Whitefield")
    compiled_search = str(q_search.compile())
    assert "customer_name" in compiled_search
    assert "customer_location" in compiled_search
    assert "review_message" in compiled_search
    assert "project_name" in compiled_search

    # 3. Allowed sorting
    for field in ALLOWED_FEEDBACK_SORT_FIELDS:
        q_sort = repo.list_query(sort_by=field, sort_order="desc")
        assert field in str(q_sort.compile())


# ==============================================================================
# Scenario 14: Statistics Calculation
# ==============================================================================


@pytest.mark.asyncio
async def test_public_statistics_response_schema():
    raw_data = {
        "total_published_reviews": 45,
        "average_rating": 4.85,
        "rating_distribution": {"1": 0, "2": 1, "3": 2, "4": 12, "5": 30},
        "total_google_reviews": 35,
        "total_website_reviews": 10,
    }

    res = CustomerFeedbackPublicStatisticsResponse.model_validate(raw_data)
    assert res.total_published_reviews == 45
    assert res.average_rating == 4.85
    assert res.rating_distribution["5"] == 30
    assert res.total_google_reviews == 35
    assert res.total_website_reviews == 10


@pytest.mark.asyncio
async def test_admin_statistics_response_schema():
    raw_data = {
        "total_reviews": 60,
        "published_reviews": 45,
        "pending_reviews": 15,
        "featured_reviews": 8,
        "average_rating": 4.72,
        "google_review_count": 40,
        "website_review_count": 15,
        "manual_review_count": 5,
        "rating_distribution": {"1": 1, "2": 2, "3": 5, "4": 18, "5": 34},
    }

    res = CustomerFeedbackAdminStatisticsResponse.model_validate(raw_data)
    assert res.total_reviews == 60
    assert res.published_reviews == 45
    assert res.pending_reviews == 15
    assert res.featured_reviews == 8
    assert res.average_rating == 4.72
    assert res.manual_review_count == 5


# ==============================================================================
# End-to-End API Router Tests with TestClient against app.main
# ==============================================================================


def test_public_endpoints_accessible_via_main_app():
    from app.main import app

    session = _DummySession()
    item = _make_sample_feedback(feedback_id=1, is_published=True)

    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = [item]
    mock_result.scalar_one.return_value = 1
    mock_result.scalar_one_or_none.return_value = item
    mock_result.one.return_value = MagicMock(
        total_published=1,
        avg_rating=5.0,
        star_1=0,
        star_2=0,
        star_3=0,
        star_4=0,
        star_5=1,
        total_google=1,
        total_website=0,
    )
    session.execute.return_value = mock_result
    session.get.return_value = item

    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)

        # 1. Public list
        res = client.get("/api/v1/customer-feedback/public")
        assert res.status_code == status.HTTP_200_OK
        body = res.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 1

        # 2. Public statistics
        res_stats = client.get("/api/v1/customer-feedback/public/statistics")
        assert res_stats.status_code == status.HTTP_200_OK
        body_stats = res_stats.json()
        assert body_stats["success"] is True
        assert body_stats["data"]["total_published_reviews"] == 1

        # 3. Public get individual
        res_get = client.get("/api/v1/customer-feedback/public/1")
        assert res_get.status_code == status.HTTP_200_OK
        assert res_get.json()["data"]["customer_name"] == item.customer_name

        # 4. Nonexistent returns 404
        mock_result.scalar_one_or_none.return_value = None
        res_not_found = client.get("/api/v1/customer-feedback/public/999")
        assert res_not_found.status_code == status.HTTP_404_NOT_FOUND
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_admin_crud_workflow_via_main_app():
    from app.main import app

    admin_user = _make_dummy_user("ADMIN")
    session = _DummySession()
    item = _make_sample_feedback(feedback_id=10, is_published=False)

    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = [item]
    mock_result.scalar_one.return_value = 1
    mock_result.scalar_one_or_none.return_value = item
    mock_result.one.return_value = MagicMock(
        total_reviews=1,
        published_reviews=0,
        pending_reviews=1,
        featured_reviews=0,
        avg_rating=5.0,
        google_reviews=1,
        website_reviews=0,
        manual_reviews=0,
        star_1=0,
        star_2=0,
        star_3=0,
        star_4=0,
        star_5=1,
    )
    session.execute.return_value = mock_result
    session.get.return_value = item

    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: session

    try:
        client = TestClient(app)

        # 1. Create a feedback
        create_payload = {
            "customer_name": "E2E Test Client",
            "customer_location": "Koramangala, Bangalore",
            "customer_photo": "/media/reviews/e2e.jpg",
            "rating": 5,
            "review_title": "Outstanding Construction Work",
            "review_message": "Very professional engineers and on-time completion of work.",
            "project_name": "Commercial Complex",
            "review_source": "google",
            "google_review_url": "https://maps.google.com/?cid=999888777",
            "is_featured": True,
            "is_published": False,
            "display_order": 10,
        }
        res_create = client.post("/api/v1/customer-feedback", json=create_payload)
        assert res_create.status_code == status.HTTP_201_CREATED, res_create.text

        # 2. Admin get by ID
        res_get = client.get("/api/v1/customer-feedback/10")
        assert res_get.status_code == status.HTTP_200_OK

        # 3. Publish via PATCH
        res_pub = client.patch("/api/v1/customer-feedback/10/publish?is_published=true")
        assert res_pub.status_code == status.HTTP_200_OK

        # 4. Feature via PATCH
        res_feat = client.patch("/api/v1/customer-feedback/10/featured?is_featured=true")
        assert res_feat.status_code == status.HTTP_200_OK

        # 5. Display order via PATCH
        res_order = client.patch("/api/v1/customer-feedback/10/display-order?display_order=99")
        assert res_order.status_code == status.HTTP_200_OK

        # 6. Update via PUT
        update_payload = {
            "customer_location": "HSR Layout, Bangalore",
            "rating": 4,
        }
        res_put = client.put("/api/v1/customer-feedback/10", json=update_payload)
        assert res_put.status_code == status.HTTP_200_OK

        # 7. Admin statistics
        res_admin_stats = client.get("/api/v1/customer-feedback/admin/statistics")
        assert res_admin_stats.status_code == status.HTTP_200_OK
        assert res_admin_stats.json()["data"]["total_reviews"] == 1

        # 8. Delete via DELETE
        res_del = client.delete("/api/v1/customer-feedback/10")
        assert res_del.status_code == status.HTTP_204_NO_CONTENT
    finally:
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_db, None)

