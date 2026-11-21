"""Website enquiry schema, rate-limit, and read-notification tests (no DB)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.exceptions import NotFoundError, TooManyRequestsError
from app.main import app as fastapi_app
from app.models.cms_enums import EnquiryStatus
from app.models.enquiry import WebsiteEnquiry
from app.schemas.enquiry import EnquiryCreate, EnquiryUnreadCount, message_preview
from app.services.enquiry_service import EnquiryService


def test_admin_enquiries_require_auth():
    client = TestClient(fastapi_app)
    assert client.get("/api/v1/admin/enquiries/unread-count").status_code == 401
    assert client.get("/api/v1/admin/enquiries").status_code == 401


def test_public_enquiry_validation_without_db():
    client = TestClient(fastapi_app)
    response = client.post("/api/v1/enquiries", json={"name": "A", "mobile": "123"})
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_enquiry_preflight_allows_json_post_from_local_static():
    client = TestClient(fastapi_app)
    for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
        response = client.options(
            "/api/v1/enquiries",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code in {200, 204}
        assert response.headers.get("access-control-allow-origin") == origin
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods.upper()


def test_enquiry_create_requires_name_and_mobile():
    with pytest.raises(ValidationError):
        EnquiryCreate(name="A", mobile="9845098765")
    with pytest.raises(ValidationError):
        EnquiryCreate(name="Ganesh Patil", mobile="12345")


def test_enquiry_create_normalizes_optional_blanks():
    payload = EnquiryCreate(
        name="  Ganesh Patil ",
        mobile="+91 9845098765",
        email="  ",
        project_type="  ",
        location="",
        construction_area=" 2500 sqft ",
        message="  Need quote  ",
    )
    assert payload.name == "Ganesh Patil"
    assert payload.mobile == "9845098765"
    assert payload.email is None
    assert payload.project_type is None
    assert payload.location is None
    assert payload.construction_area == "2500 sqft"
    assert payload.message == "Need quote"


def test_message_preview_truncates():
    assert message_preview(None) is None
    assert message_preview("short") == "short"
    long = "x" * 200
    preview = message_preview(long)
    assert preview is not None
    assert len(preview) == 120
    assert preview.endswith("…")


@pytest.mark.asyncio
async def test_create_public_rate_limits_same_mobile():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    service = EnquiryService(session)
    service.repo.recent_count_for_mobile = AsyncMock(return_value=3)

    payload = EnquiryCreate(name="Ganesh Patil", mobile="9845098765")
    with pytest.raises(TooManyRequestsError):
        await service.create_public(payload, ip_address="1.1.1.1", user_agent="test")
    session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_create_public_saves_new_unread():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    service = EnquiryService(session)
    service.repo.recent_count_for_mobile = AsyncMock(return_value=0)

    saved = WebsiteEnquiry(
        name="Ganesh Patil",
        mobile="9845098765",
        status=EnquiryStatus.NEW.value,
        is_read=False,
    )
    saved.id = 11
    saved.created_at = datetime.now(timezone.utc)

    async def add(item):
        item.id = saved.id
        item.created_at = saved.created_at
        return item

    service.repo.add = AsyncMock(side_effect=add)
    payload = EnquiryCreate(name="Ganesh Patil", mobile="9845098765")
    out = await service.create_public(payload)
    assert out.id == 11
    session.commit.assert_awaited()
    added = service.repo.add.await_args.args[0]
    assert added.is_read is False
    assert added.status == EnquiryStatus.NEW.value


@pytest.mark.asyncio
async def test_get_admin_marks_new_enquiry_read():
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    item = WebsiteEnquiry(
        name="Ganesh Patil",
        mobile="9845098765",
        status=EnquiryStatus.NEW.value,
        is_read=False,
        source="WEBSITE",
    )
    item.id = 5
    now = datetime.now(timezone.utc)
    item.created_at = now
    item.updated_at = now

    service = EnquiryService(session)
    service.repo.get = AsyncMock(return_value=item)
    out = await service.get_admin(5)
    assert item.is_read is True
    assert item.status == EnquiryStatus.READ.value
    assert out.is_read is True
    session.commit.assert_awaited()


@pytest.mark.asyncio
async def test_get_admin_missing_raises():
    session = MagicMock()
    service = EnquiryService(session)
    service.repo.get = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError):
        await service.get_admin(99)


@pytest.mark.asyncio
async def test_unread_count_wraps_repo():
    session = MagicMock()
    service = EnquiryService(session)
    service.repo.unread_count = AsyncMock(return_value=4)
    data = await service.unread_count()
    assert data == EnquiryUnreadCount(unread_count=4)
