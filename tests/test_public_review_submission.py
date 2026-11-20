"""Comprehensive tests for Phase 3 - Public Customer Review API.

Covers all 18 requirements specified in the prompt:
1. Public submission without JWT
2. Valid JSON submission
3. Valid multipart submission with photo
4. Empty customer name validation
5. Empty customer location validation
6. Empty review message validation
7. Invalid rating validation (0, 6, 4.5, "abc", bool)
8. Invalid photo format rejection
9. SVG rejection
10. Image larger than 5 MB rejection
11. Customer cannot control is_published (always True on server)
12. Customer cannot control is_featured (always False on server)
13. Successful review saved in MySQL / database session
14. is_published is True after submission
15. review_source is "website"
16. Review appears in existing public GET API
17. Admin APIs still require Admin JWT
18. Existing Admin CRUD operations still work

Additional security tests:
- Rate limiting protection (HTTP 429)
- Duplicate rapid-submission protection (HTTP 422)
- Anti-spam honeypot detection (HTTP 422)
- XSS / script tag sanitization
"""

from __future__ import annotations

import io
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from app.api.deps import require_admin
from app.api.routes.customer_feedback import router as feedback_router
from app.core.database import AsyncSessionLocal, engine, get_db
from app.core.exceptions import register_exception_handlers
from app.models.cms_enums import MediaFolder
from app.models.customer_feedback import CustomerFeedback, ReviewSource
from app.models.user import Role, User
from app.schemas.customer_feedback import (
    CustomerFeedbackPublicResponse,
    CustomerReviewPublicSubmit,
)
from app.services.customer_feedback_service import CustomerFeedbackService
from app.services.media_storage import MediaSettings, MediaStorageService
from app.services.review_rate_limiter import get_review_tracker

# Sample valid images
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 100
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
SVG_BYTES = b"<svg xmlns='http://www.w3.org/2000/svg'><circle r='5'/></svg>"
TEXT_BYTES = b"This is just a text file pretending to be an image"


class _MockDbSession:
    def __init__(self):
        self.added_items: list[CustomerFeedback] = []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.flush = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock()
        self.execute = AsyncMock()
        self.execute.return_value.scalar_one_or_none.return_value = None

    def add(self, item: CustomerFeedback):
        if getattr(item, "id", None) is None:
            item.id = len(self.added_items) + 100
        if getattr(item, "created_at", None) is None:
            item.created_at = datetime.now(timezone.utc)
        if getattr(item, "updated_at", None) is None:
            item.updated_at = datetime.now(timezone.utc)
        self.added_items.append(item)

    async def refresh(self, item: CustomerFeedback):
        if getattr(item, "id", None) is None:
            item.id = 100
        if getattr(item, "created_at", None) is None:
            item.created_at = datetime.now(timezone.utc)
        if getattr(item, "updated_at", None) is None:
            item.updated_at = datetime.now(timezone.utc)


def _make_admin_user() -> User:
    role = Role(id=1, name="ADMIN")
    user = User(
        id=1,
        name="Admin Test",
        email="admin@mkconstruction.in",
        password_hash="fake",
        role_id=1,
        is_active=True,
    )
    user.role = role
    return user


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter and duplicate tracker before every test."""
    get_review_tracker().sync_reset()
    yield
    get_review_tracker().sync_reset()


@pytest.fixture
def test_app():
    """Create test FastAPI application with feedback routes."""
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(feedback_router, prefix="/api/v1")
    return app


# ==============================================================================
# Requirement 1: Public Submission Without JWT
# ==============================================================================


def test_public_submission_without_jwt(test_app):
    """Customers must be able to submit reviews without logging in or sending JWT."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session

    client = TestClient(test_app)
    payload = {
        "customer_name": "Ravi Kumar",
        "customer_location": "Coimbatore, Tamil Nadu",
        "rating": 5,
        "review_title": "Dream Home Completed",
        "review_message": "MK Construction constructed our family house with precision and quality.",
    }

    # Submit without any Authorization header
    response = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["success"] is True
    assert data["data"]["customer_name"] == "Ravi Kumar"
    assert data["data"]["rating"] == 5
    assert len(session.added_items) == 1


# ==============================================================================
# Requirement 2: Valid JSON Submission
# ==============================================================================


def test_valid_json_submission(test_app):
    """Valid review submitted via application/json must succeed."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session

    client = TestClient(test_app)
    payload = {
        "customer_name": "Suresh Raina",
        "customer_location": "Chennai",
        "rating": 4,
        "review_title": "Great Team",
        "review_message": "Timely handover of the duplex project. Very cooperative team.",
    }

    response = client.post(
        "/api/v1/customer-feedback/public/submit",
        json=payload,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["data"]["customer_name"] == "Suresh Raina"
    assert body["data"]["customer_location"] == "Chennai"
    assert body["data"]["rating"] == 4
    assert body["data"]["review_message"] == "Timely handover of the duplex project. Very cooperative team."


# ==============================================================================
# Requirement 3: Valid Multipart Submission With Photo
# ==============================================================================


def test_valid_multipart_submission_with_photo(test_app, tmp_path):
    """Valid review submitted via multipart/form-data with photo upload."""
    session = _MockDbSession()
    media_settings = MediaSettings(
        media_root=tmp_path / "media_storage",
        url_prefix="/media",
        public_base_url=None,
        max_file_size_bytes=5 * 1024 * 1024,
        max_batch_size=20,
    )
    storage = MediaStorageService(media_settings)

    test_app.dependency_overrides[get_db] = lambda: session

    # Temporarily patch service storage in app
    orig_init = CustomerFeedbackService.__init__

    def patched_init(self, db, s=None):
        orig_init(self, db, storage)

    CustomerFeedbackService.__init__ = patched_init

    try:
        client = TestClient(test_app)
        files = {
            "customer_photo": ("avatar.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg"),
        }
        data = {
            "customer_name": "Kavitha M",
            "customer_location": "Madurai",
            "rating": "5",
            "review_title": "Superb Craftsmanship",
            "review_message": "Built our commercial showroom flawlessly. Highly recommended!",
        }

        response = client.post("/api/v1/customer-feedback/public/submit", data=data, files=files)
        assert response.status_code == status.HTTP_201_CREATED, response.text
        body = response.json()
        assert body["data"]["customer_name"] == "Kavitha M"
        assert body["data"]["customer_photo"] is not None
        assert body["data"]["customer_photo"].startswith("/media/reviews/")
        assert body["data"]["customer_photo"].endswith(".jpg")
    finally:
        CustomerFeedbackService.__init__ = orig_init


# ==============================================================================
# Requirement 4, 5, 6: Empty Name, Location, Message Validation
# ==============================================================================


def test_empty_customer_name_rejected(test_app):
    """Empty or whitespace-only customer_name must be rejected with 422."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    # Empty string
    res1 = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "", "customer_location": "Madurai", "rating": 5, "review_message": "Msg"},
    )
    assert res1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Whitespace only
    res2 = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "   ", "customer_location": "Madurai", "rating": 5, "review_message": "Msg"},
    )
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_empty_customer_location_rejected(test_app):
    """Empty or whitespace-only customer_location must be rejected with 422."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "   ", "rating": 5, "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_empty_review_message_rejected(test_app):
    """Empty or whitespace-only review_message must be rejected with 422."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": 5, "review_message": "  \n  "},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# Requirement 7: Invalid Rating Validation
# ==============================================================================


def test_invalid_rating_rejected(test_app):
    """Ratings outside 1-5, floats, non-integers, or booleans must be rejected."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    # Rating 0 (too low)
    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": 0, "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Rating 6 (too high)
    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": 6, "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Rating float 4.5
    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": 4.5, "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Rating non-number string "five"
    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": "five", "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Rating boolean True
    res = client.post(
        "/api/v1/customer-feedback/public/submit",
        json={"customer_name": "Ravi", "customer_location": "Madurai", "rating": True, "review_message": "Msg"},
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# Requirement 8, 9, 10: Photo Security (Invalid Format, SVG, > 5MB)
# ==============================================================================


def test_invalid_photo_format_rejected(test_app, tmp_path):
    """Text files or unapproved formats disguised as images must be rejected."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    files = {
        "customer_photo": ("document.txt", io.BytesIO(TEXT_BYTES), "text/plain"),
    }
    data = {
        "customer_name": "Anand",
        "customer_location": "Trichy",
        "rating": "5",
        "review_message": "Good experience overall.",
    }
    response = client.post("/api/v1/customer-feedback/public/submit", data=data, files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_svg_photo_rejected(test_app):
    """SVG photos must be rejected for security (XSS prevention)."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    files = {
        "customer_photo": ("avatar.svg", io.BytesIO(SVG_BYTES), "image/svg+xml"),
    }
    data = {
        "customer_name": "Anand",
        "customer_location": "Trichy",
        "rating": "5",
        "review_message": "Good experience overall.",
    }
    response = client.post("/api/v1/customer-feedback/public/submit", data=data, files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_image_larger_than_5mb_rejected(test_app):
    """Images larger than 5 MB must be rejected with 422."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    # 5.1 MB of data
    large_data = JPEG_BYTES + b"\x00" * (5 * 1024 * 1024 + 100)
    files = {
        "customer_photo": ("large.jpg", io.BytesIO(large_data), "image/jpeg"),
    }
    data = {
        "customer_name": "Anand",
        "customer_location": "Trichy",
        "rating": "5",
        "review_message": "Good experience overall.",
    }
    response = client.post("/api/v1/customer-feedback/public/submit", data=data, files=files)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# Requirement 11 & 12: Customer Cannot Control is_published or is_featured
# ==============================================================================


def test_customer_cannot_control_is_published_or_is_featured(test_app):
    """Client attempts to send is_published=False or is_featured=True must be ignored."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    payload = {
        "customer_name": "Vikram",
        "customer_location": "Salem",
        "rating": 5,
        "review_message": "Great builder, delivered on schedule.",
        "is_published": False,  # Customer attempts to set unpublished
        "is_featured": True,    # Customer attempts to feature themselves
        "review_source": "google",  # Customer attempts to fake google source
        "display_order": 999,   # Customer attempts to manipulate order
    }

    response = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    # Verify saved entity in database session
    assert len(session.added_items) == 1
    saved = session.added_items[0]
    assert saved.is_published is True  # Enforced to True!
    assert saved.is_featured is False  # Enforced to False!
    assert saved.review_source == "website"  # Enforced to website!
    assert saved.display_order == 0  # Enforced to 0!


# ==============================================================================
# Requirement 13, 14, 15: Successful Review Saved in MySQL, is_published, review_source
# ==============================================================================


@pytest.mark.asyncio
async def test_successful_review_saved_with_server_values():
    """Verify CustomerFeedbackService saves item with is_published=True and review_source='website'."""
    session = _MockDbSession()
    service = CustomerFeedbackService(session)

    payload = CustomerReviewPublicSubmit(
        customer_name="Deepak V",
        customer_location="Erode",
        rating=5,
        review_title="Excellent Finish",
        review_message="Structural integrity and elevation design are top class.",
    )

    result = await service.submit_public_review(payload=payload, client_ip="192.168.1.100")
    session.commit.assert_awaited_once()

    assert len(session.added_items) == 1
    saved = session.added_items[0]
    assert saved.customer_name == "Deepak V"
    assert saved.customer_location == "Erode"
    assert saved.rating == 5
    assert saved.is_published is True
    assert saved.review_source == "website"
    assert saved.is_featured is False
    assert saved.display_order == 0
    assert saved.review_date == date.today()
    assert result.customer_name == "Deepak V"


# ==============================================================================
# Requirement 16: Review Appears in Existing Public GET API
# ==============================================================================


def test_review_appears_in_existing_public_get_api(test_app):
    """Submitted review is immediately published and accessible via GET /public."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    # 1. Submit review
    payload = {
        "customer_name": "Manoj Kumar",
        "customer_location": "Tirupur",
        "rating": 5,
        "review_message": "Quality of construction materials used is superior.",
    }
    submit_res = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert submit_res.status_code == status.HTTP_201_CREATED
    saved_item = session.added_items[0]

    # 2. Mock query result for GET /public to return this published item
    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = [saved_item]
    mock_result.scalar_one.return_value = 1
    session.execute.return_value = mock_result

    get_res = client.get("/api/v1/customer-feedback/public")
    assert get_res.status_code == status.HTTP_200_OK
    data = get_res.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["customer_name"] == "Manoj Kumar"
    assert data["items"][0]["review_source"] == "website"


# ==============================================================================
# Requirement 17: Admin APIs Still Require Admin JWT
# ==============================================================================


def test_admin_apis_still_require_admin_jwt(test_app):
    """Unauthenticated requests to admin customer feedback endpoints must return 401."""
    client = TestClient(test_app)

    # Admin listing
    res = client.get("/api/v1/customer-feedback")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Admin statistics
    res = client.get("/api/v1/customer-feedback/admin/statistics")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Admin create
    res = client.post("/api/v1/customer-feedback", json={"customer_name": "Test"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Admin publish status
    res = client.patch("/api/v1/customer-feedback/1/publish?is_published=true")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # Admin delete
    res = client.delete("/api/v1/customer-feedback/1")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# Requirement 18: Existing Admin CRUD Operations Still Work
# ==============================================================================


def test_existing_admin_crud_operations_still_work(test_app):
    """Existing Admin CRUD endpoints must continue to work when authenticated."""
    admin_user = _make_admin_user()
    session = _MockDbSession()
    item = CustomerFeedback(
        customer_name="Existing Client",
        customer_location="Bangalore",
        customer_photo="/media/reviews/test.jpg",
        rating=5,
        review_title="Super",
        review_message="Great work.",
        project_name="Villa 1",
        review_source="google",
        review_date=date.today(),
        is_featured=False,
        is_published=True,
        display_order=0,
    )
    item.id = 55
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)

    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = [item]
    mock_result.scalar_one.return_value = 1
    mock_result.scalar_one_or_none.return_value = item
    session.execute.return_value = mock_result
    session.get.return_value = item

    test_app.dependency_overrides[require_admin] = lambda: admin_user
    test_app.dependency_overrides[get_db] = lambda: session

    client = TestClient(test_app)

    # 1. Admin GET by ID
    res = client.get("/api/v1/customer-feedback/55")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["data"]["customer_name"] == "Existing Client"

    # 2. Admin PATCH publish
    res_pub = client.patch("/api/v1/customer-feedback/55/publish?is_published=false")
    assert res_pub.status_code == status.HTTP_200_OK

    # 3. Admin PATCH featured
    res_feat = client.patch("/api/v1/customer-feedback/55/featured?is_featured=true")
    assert res_feat.status_code == status.HTTP_200_OK

    # 4. Admin DELETE
    res_del = client.delete("/api/v1/customer-feedback/55")
    assert res_del.status_code == status.HTTP_204_NO_CONTENT


# ==============================================================================
# Security & Spam Protection: Rate Limiting, Duplicates, Honeypot
# ==============================================================================


def test_rate_limiting_exceeded(test_app):
    """More than 5 requests from same IP within window must return HTTP 429."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    headers = {"X-Forwarded-For": "203.0.113.195"}

    for i in range(5):
        payload = {
            "customer_name": f"User {i}",
            "customer_location": "Coimbatore",
            "rating": 5,
            "review_message": f"Review number {i} is unique.",
        }
        res = client.post("/api/v1/customer-feedback/public/submit", json=payload, headers=headers)
        assert res.status_code == status.HTTP_201_CREATED

    # 6th request from same IP should be rate limited
    payload_6th = {
        "customer_name": "User 6",
        "customer_location": "Coimbatore",
        "rating": 5,
        "review_message": "Review number 6 should be blocked.",
    }
    res_blocked = client.post("/api/v1/customer-feedback/public/submit", json=payload_6th, headers=headers)
    assert res_blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    body = res_blocked.json()
    assert body["success"] is False
    assert "Rate limit exceeded" in body["message"]


def test_duplicate_rapid_submission_protection(test_app):
    """Submitting the exact same review within 2 minutes must be rejected as duplicate."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    payload = {
        "customer_name": "Duplicate Tester",
        "customer_location": "Coimbatore",
        "rating": 5,
        "review_message": "Identical review message posted twice.",
    }

    # First attempt: succeeds
    res1 = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert res1.status_code == status.HTTP_201_CREATED

    # Second attempt (rapid duplicate): rejected
    res2 = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert res2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Duplicate review detected" in res2.json()["message"]


def test_honeypot_bot_protection(test_app):
    """Honeypot field filled by spambots must cause rejection."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    payload = {
        "customer_name": "Spam Bot",
        "customer_location": "Spam City",
        "rating": 5,
        "review_message": "Spam message buy online now.",
        "honeypot": "http://spamsite.xyz",  # Hidden field filled by bot
    }

    res = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_script_tag_injection_rejected(test_app):
    """Review with embedded script tags must be rejected."""
    session = _MockDbSession()
    test_app.dependency_overrides[get_db] = lambda: session
    client = TestClient(test_app)

    payload = {
        "customer_name": "<script>alert('xss')</script>",
        "customer_location": "Coimbatore",
        "rating": 5,
        "review_message": "Normal message",
    }
    res = client.post("/api/v1/customer-feedback/public/submit", json=payload)
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# Live MySQL Database Verification
# ==============================================================================


@pytest.mark.asyncio
async def test_live_mysql_persistence():
    """Verify insertion directly into local MySQL database."""
    async with AsyncSessionLocal() as session:
        service = CustomerFeedbackService(session)
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        test_name = f"Live MySQL Customer {timestamp_str}"

        payload = CustomerReviewPublicSubmit(
            customer_name=test_name,
            customer_location="Coimbatore South",
            rating=5,
            review_title="Live DB Test",
            review_message="This review verifies real persistence in the MySQL customer_feedback table.",
        )

        res = await service.submit_public_review(payload, client_ip="127.0.0.1")
        assert res.id is not None
        assert res.customer_name == test_name
        assert res.review_source == "website"
        assert res.is_featured is False
        assert res.display_order == 0

        # Query back directly from MySQL using raw SQL
        check_stmt = text("SELECT is_published, review_source, is_featured, display_order FROM customer_feedback WHERE id = :id")
        result = (await session.execute(check_stmt, {"id": res.id})).one()
        assert result[0] == 1  # is_published is True (1 in MySQL)
        assert result[1] == "website"  # review_source is "website"
        assert result[2] == 0  # is_featured is False (0 in MySQL)
        assert result[3] == 0  # display_order is 0

        # Clean up test row
        del_stmt = text("DELETE FROM customer_feedback WHERE id = :id")
        await session.execute(del_stmt, {"id": res.id})
        await session.commit()
