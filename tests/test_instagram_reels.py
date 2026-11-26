"""Comprehensive tests for Instagram Reels Management module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.deps import get_current_user, require_admin
from app.api.routes import instagram_reels as reels_routes
from app.core.database import Base, get_db
from app.core.exceptions import ConflictError, DatabaseError, NotFoundError, ValidationFailedError
from app.models.instagram_reel import InstagramReel, InstagramSectionSettings
from app.models.user import Role, User
from app.repositories.instagram_reel_repository import InstagramReelRepository
from app.schemas.instagram_reel import (
    InstagramReelCreate,
    InstagramReelOrderUpdate,
    InstagramReelOut,
    InstagramReelPublicListOut,
    InstagramReelPublicOut,
    InstagramReelPublishUpdate,
    InstagramReelUpdate,
    InstagramSectionSettingsOut,
    InstagramSectionSettingsUpdate,
    parse_and_normalize_instagram_url,
)
from app.services.instagram_reel_service import InstagramReelService


class _NestedTx:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummySession:
    def __init__(self):
        self.add = MagicMock()
        self.flush = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock()
        self.execute = AsyncMock()
        self.begin_nested = MagicMock(return_value=_NestedTx())

        async def _refresh(item):
            now = datetime.now(timezone.utc)
            if getattr(item, "id", None) is None:
                item.id = 1
            if hasattr(item, "created_at") and getattr(item, "created_at", None) is None:
                item.created_at = now
            if hasattr(item, "updated_at") and getattr(item, "updated_at", None) is None:
                item.updated_at = now

        self.refresh = AsyncMock(side_effect=_refresh)


def _make_user(role_name: str = "ADMIN") -> User:
    role = Role(id=1, name=role_name)
    user = User(
        id=1,
        name="Admin User",
        email="admin@mkconstruction.in",
        password_hash="hashed",
        role_id=1,
        is_active=True,
    )
    user.role = role
    return user


def _make_reel(
    reel_id: int = 1,
    *,
    title: str = "Villa Tour",
    shortcode: str = "C9xYzAb1234",
    is_published: bool = True,
    display_order: int = 0,
    description: str | None = "Luxury duplex walkthrough",
) -> InstagramReel:
    now = datetime.now(timezone.utc)
    reel = InstagramReel(
        title=title,
        instagram_url=f"https://www.instagram.com/reel/{shortcode}/",
        embed_url=f"https://www.instagram.com/reel/{shortcode}/embed/",
        description=description,
        is_published=is_published,
        display_order=display_order,
    )
    reel.id = reel_id
    reel.created_at = now
    reel.updated_at = now
    return reel


def _make_settings(is_enabled: bool = True) -> InstagramSectionSettings:
    settings = InstagramSectionSettings(id=1, is_enabled=is_enabled)
    settings.updated_at = datetime.now(timezone.utc)
    return settings


# ==============================================================================
# 1. Database Model Metadata & Singleton Constraint Tests (SQLite DDL)
# ==============================================================================


def test_models_tables_indexes_and_singleton_constraint():
    """Verify table names, indexes, and DB-level singleton & non-negative constraints."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[InstagramReel.__table__, InstagramSectionSettings.__table__],
    )
    inspector = inspect(engine)
    reel_indexes = {idx["name"] for idx in inspector.get_indexes("instagram_reels")}
    assert "ix_instagram_reels_pub_order" in reel_indexes

    with engine.begin() as conn:
        # Singleton id=1 succeeds
        conn.execute(text("INSERT INTO instagram_section_settings (id, is_enabled) VALUES (1, 1)"))

        # Duplicate id=1 fails on PK
        with pytest.raises(IntegrityError):
            conn.execute(
                text("INSERT INTO instagram_section_settings (id, is_enabled) VALUES (1, 0)")
            )

    with engine.begin() as conn:
        # Non-1 id fails on CHECK constraint (id = 1)
        with pytest.raises(IntegrityError):
            conn.execute(
                text("INSERT INTO instagram_section_settings (id, is_enabled) VALUES (2, 1)")
            )

    with engine.begin() as conn:
        # Negative display_order fails on CHECK constraint
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    "INSERT INTO instagram_reels "
                    "(title, instagram_url, embed_url, is_published, display_order) "
                    "VALUES ('T', 'https://www.instagram.com/reel/Abcd1234/', "
                    "'https://www.instagram.com/reel/Abcd1234/embed/', 0, -1)"
                )
            )


# ==============================================================================
# 2. Instagram URL Validation & Normalization Tests
# ==============================================================================


@pytest.mark.parametrize(
    ("raw_url", "expected_canonical", "expected_embed"),
    [
        (
            "https://instagram.com/reel/C8xYzAb1234/",
            "https://www.instagram.com/reel/C8xYzAb1234/",
            "https://www.instagram.com/reel/C8xYzAb1234/embed/",
        ),
        (
            "https://www.instagram.com/reel/C8xYzAb1234",
            "https://www.instagram.com/reel/C8xYzAb1234/",
            "https://www.instagram.com/reel/C8xYzAb1234/embed/",
        ),
        (
            "  https://m.instagram.com/reels/AbCd_12-34/?igsh=MzRlODBiNWFlZA==  ",
            "https://www.instagram.com/reel/AbCd_12-34/",
            "https://www.instagram.com/reel/AbCd_12-34/embed/",
        ),
        (
            "HTTPS://WWW.INSTAGRAM.COM/p/PostCode99/?utm_source=ig_web_copy_link#frag",
            "https://www.instagram.com/p/PostCode99/",
            "https://www.instagram.com/p/PostCode99/embed/",
        ),
    ],
)
def test_instagram_url_valid_and_normalized(raw_url, expected_canonical, expected_embed):
    canonical, embed, _ = parse_and_normalize_instagram_url(raw_url)
    assert canonical == expected_canonical
    assert embed == expected_embed


@pytest.mark.parametrize(
    "bad_url",
    [
        "",
        "   ",
        "http://www.instagram.com/reel/C8xYzAb1234/",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "https://evil.com/reel/C8xYzAb1234/",
        "https://evil.instagram.com/reel/C8xYzAb1234/",
        "https://instagram.com.evil.com/reel/C8xYzAb1234/",
        "https://user:pass@www.instagram.com/reel/C8xYzAb1234/",
        "https://www.instagram.com:8443/reel/C8xYzAb1234/",
        "https://www.instagram.com/stories/user/1234567/",
        "https://www.instagram.com/tv/C8xYzAb1234/",
        "https://www.instagram.com/username/reel/C8xYzAb1234/",
        "https://www.instagram.com/reel/C8xYzAb1234/extra/",
        "https://www.instagram.com/reel//C8xYzAb1234/",
        "https://www.instagram.com/reel/",
        "https://www.instagram.com/reel/ab/",
        "https://www.instagram.com/reel/----/",
        "https://www.instagram.com/reel/bad.code/",
        "https://www.instagram.com/reel/bad%2Fcode/",
        "https://www.instagram.com/reel/bad code/",
        "https://www.instagram.com\\reel/C8xYzAb1234/",
        "not-a-url",
    ],
)
def test_instagram_url_rejects_invalid_and_unsafe_inputs(bad_url):
    with pytest.raises(ValueError):
        parse_and_normalize_instagram_url(bad_url)


# ==============================================================================
# 3. Pydantic Schema Validation Tests
# ==============================================================================


def test_schema_validation_rules():
    # Valid create
    created = InstagramReelCreate(
        title="  Modern Villa Foundation  ",
        instagram_url="https://m.instagram.com/reels/C8xYzAb1234/?igsh=123",
        description="  ",
        is_published=True,
        display_order=2,
    )
    assert created.title == "Modern Villa Foundation"
    assert created.instagram_url == "https://www.instagram.com/reel/C8xYzAb1234/"
    assert created.description is None
    assert created.is_published is True
    assert created.display_order == 2

    # Title length / whitespace
    with pytest.raises(ValidationError):
        InstagramReelCreate(title="   ", instagram_url="https://instagram.com/reel/Abcd1234/")
    with pytest.raises(ValidationError):
        InstagramReelCreate(
            title="x" * 201, instagram_url="https://instagram.com/reel/Abcd1234/"
        )

    # Negative and boolean display_order
    with pytest.raises(ValidationError):
        InstagramReelCreate(
            title="Valid",
            instagram_url="https://instagram.com/reel/Abcd1234/",
            display_order=-1,
        )
    with pytest.raises(ValidationError):
        InstagramReelCreate(
            title="Valid",
            instagram_url="https://instagram.com/reel/Abcd1234/",
            display_order=True,  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        InstagramReelOrderUpdate(display_order=-5)
    with pytest.raises(ValidationError):
        InstagramReelOrderUpdate(display_order=False)  # type: ignore[arg-type]

    # Boolean validation
    with pytest.raises(ValidationError):
        InstagramReelPublishUpdate(is_published="not-a-bool")  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        InstagramSectionSettingsUpdate(is_enabled=2)  # type: ignore[arg-type]

    # Empty update payload rejected
    with pytest.raises(ValidationError, match="At least one field"):
        InstagramReelUpdate()

    # Null on non-nullable fields rejected
    with pytest.raises(ValidationError, match="cannot be null"):
        InstagramReelUpdate(title=None)
    with pytest.raises(ValidationError, match="cannot be null"):
        InstagramReelUpdate(is_published=None)

    # Clearing nullable description is allowed
    clear_desc = InstagramReelUpdate(description=None)
    assert "description" in clear_desc.model_fields_set
    assert clear_desc.description is None


# ==============================================================================
# 4. Repository Tests
# ==============================================================================


def test_repository_list_query_filters_and_sorting():
    repo = InstagramReelRepository(_DummySession())  # type: ignore[arg-type]

    pub_stmt = repo.list_query(published_only=True, sort_by="display_order", sort_order="asc")
    pub_sql = str(pub_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "instagram_reels.is_published" in pub_sql
    assert "ORDER BY instagram_reels.display_order ASC" in pub_sql

    search_stmt = repo.list_query(search="villa", is_published=False)
    search_sql = str(search_stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "instagram_reels.title" in search_sql
    assert "instagram_reels.description" in search_sql
    assert "instagram_reels.instagram_url" in search_sql


@pytest.mark.asyncio
async def test_repository_get_or_create_settings_handles_race_condition():
    session = _DummySession()
    repo = InstagramReelRepository(session)  # type: ignore[arg-type]

    winning_row = _make_settings(is_enabled=True)
    # 1st get_settings -> None, flush -> IntegrityError, 2nd get_settings -> winning_row
    repo.get_settings = AsyncMock(side_effect=[None, winning_row])  # type: ignore[method-assign]
    session.flush = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("dup pk")))

    settings, created = await repo.get_or_create_settings()
    assert created is False
    assert settings.id == 1
    assert settings.is_enabled is True
    assert repo.get_settings.await_count == 2


# ==============================================================================
# 5. Service Layer Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_service_create_update_publish_order_and_delete():
    session = _DummySession()
    service = InstagramReelService(session)  # type: ignore[arg-type]

    created = await service.create(
        InstagramReelCreate(
            title="Site Walkthrough",
            instagram_url="https://instagram.com/reels/WalkThru123/",
            description="Foundation day",
            is_published=False,
            display_order=3,
        )
    )
    session.commit.assert_awaited_once()
    assert created.instagram_url == "https://www.instagram.com/reel/WalkThru123/"
    assert created.embed_url == "https://www.instagram.com/reel/WalkThru123/embed/"
    assert created.is_published is False

    # Update URL regenerates embed_url
    reel = _make_reel(reel_id=5, shortcode="OldCode1234", is_published=False)
    service.repo.get = AsyncMock(return_value=reel)  # type: ignore[method-assign]
    updated = await service.update(
        5, InstagramReelUpdate(instagram_url="https://www.instagram.com/p/NewPost5678/")
    )
    assert updated.instagram_url == "https://www.instagram.com/p/NewPost5678/"
    assert updated.embed_url == "https://www.instagram.com/p/NewPost5678/embed/"

    # Publish toggle
    published = await service.set_publish_status(5, True)
    assert published.is_published is True

    # Display order update
    ordered = await service.set_display_order(5, 1)
    assert ordered.display_order == 1

    # Negative display order guard
    with pytest.raises(ValidationFailedError):
        await service.set_display_order(5, -1)

    # Delete
    await service.delete(5)
    session.delete.assert_awaited_once_with(reel)


@pytest.mark.asyncio
async def test_service_error_and_rollback_handling():
    session = _DummySession()
    service = InstagramReelService(session)  # type: ignore[arg-type]

    service.repo.get = AsyncMock(return_value=None)  # type: ignore[method-assign]
    with pytest.raises(NotFoundError):
        await service.get_admin(999)

    session.commit = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("constraint")))
    with pytest.raises(ConflictError):
        await service.create(
            InstagramReelCreate(
                title="Conflict Test",
                instagram_url="https://www.instagram.com/reel/Abcd1234/",
            )
        )
    session.rollback.assert_awaited_once()

    session.rollback.reset_mock()
    session.commit = AsyncMock(side_effect=SQLAlchemyError("db down"))
    with pytest.raises(DatabaseError):
        await service.create(
            InstagramReelCreate(
                title="DB Err Test",
                instagram_url="https://www.instagram.com/reel/Abcd1234/",
            )
        )
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_service_list_public_when_disabled_and_enabled():
    session = _DummySession()
    service = InstagramReelService(session)  # type: ignore[arg-type]

    # Disabled section returns empty list without querying reels
    service.repo.get_or_create_settings = AsyncMock(  # type: ignore[method-assign]
        return_value=(_make_settings(is_enabled=False), False)
    )
    disabled_res = await service.list_public(page=1, page_size=10)
    assert isinstance(disabled_res, InstagramReelPublicListOut)
    assert disabled_res.is_enabled is False
    assert disabled_res.items == []
    assert disabled_res.total == 0
    assert disabled_res.total_pages == 0
    session.execute.assert_not_called()

    # Enabled section returns published items sorted by display_order with public fields only
    reel1 = _make_reel(reel_id=1, title="First", shortcode="First1234", display_order=0)
    reel2 = _make_reel(reel_id=2, title="Second", shortcode="Second567", display_order=1)

    count_res = MagicMock()
    count_res.scalar_one.return_value = 2
    items_res = MagicMock()
    items_res.unique.return_value.scalars.return_value.all.return_value = [reel1, reel2]
    session.execute = AsyncMock(side_effect=[count_res, items_res])

    service.repo.get_or_create_settings = AsyncMock(  # type: ignore[method-assign]
        return_value=(_make_settings(is_enabled=True), False)
    )
    enabled_res = await service.list_public(page=1, page_size=10)
    assert enabled_res.is_enabled is True
    assert enabled_res.total == 2
    assert enabled_res.total_pages == 1
    assert [i.id for i in enabled_res.items] == [1, 2]
    assert isinstance(enabled_res.items[0], InstagramReelPublicOut)
    assert not hasattr(enabled_res.items[0], "is_published")
    assert not hasattr(enabled_res.items[0], "created_at")


# ==============================================================================
# 6. Route Contract, RBAC & End-to-End TestClient Tests
# ==============================================================================


def test_routes_registered_and_rbac_enforced():
    from app.main import app

    paths = set(app.openapi()["paths"].keys())
    expected_paths = {
        "/api/v1/public/instagram-reels",
        "/api/v1/admin/instagram-reels",
        "/api/v1/admin/instagram-reels/settings",
        "/api/v1/admin/instagram-reels/{id}",
        "/api/v1/admin/instagram-reels/{id}/publish",
        "/api/v1/admin/instagram-reels/{id}/order",
    }
    assert not (expected_paths - paths)

    # Public route has no auth dependency
    for route in reels_routes.public_router.routes:
        if isinstance(route, APIRoute):
            dep_names = {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}
            assert "require_admin" not in dep_names
            assert "get_current_user" not in dep_names

    # All admin routes require require_admin and static /settings precedes /{id}
    admin_routes = [r for r in reels_routes.admin_router.routes if isinstance(r, APIRoute)]
    assert len(admin_routes) == 9
    for route in admin_routes:
        dep_names = {getattr(d.call, "__name__", "") for d in route.dependant.dependencies}
        assert "require_admin" in dep_names, f"{route.path} missing require_admin"

    admin_paths_in_order = [r.path for r in admin_routes]
    settings_idx = admin_paths_in_order.index("/admin/instagram-reels/settings")
    id_idx = admin_paths_in_order.index("/admin/instagram-reels/{id}")
    assert settings_idx < id_idx


def test_admin_routes_reject_unauthenticated_and_non_admin():
    from app.main import app

    client = TestClient(app)
    assert client.get("/api/v1/admin/instagram-reels").status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        client.get("/api/v1/admin/instagram-reels/settings").status_code
        == status.HTTP_401_UNAUTHORIZED
    )
    assert client.post("/api/v1/admin/instagram-reels", json={}).status_code == 401

    viewer = _make_user("VIEWER")
    app.dependency_overrides[get_current_user] = lambda: viewer
    try:
        assert client.get("/api/v1/admin/instagram-reels").status_code == status.HTTP_403_FORBIDDEN
        assert (
            client.put("/api/v1/admin/instagram-reels/settings", json={"is_enabled": False}).status_code
            == status.HTTP_403_FORBIDDEN
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_public_and_admin_endpoints_e2e_via_main_app():
    from app.main import app

    admin_user = _make_user("ADMIN")
    session = _DummySession()
    reel = _make_reel(reel_id=7, is_published=True, display_order=1)
    settings_row = _make_settings(is_enabled=True)

    mock_result = MagicMock()
    mock_result.unique.return_value.scalars.return_value.all.return_value = [reel]
    mock_result.scalar_one.return_value = 1
    mock_result.scalar_one_or_none.return_value = settings_row
    session.execute.return_value = mock_result
    session.get.return_value = reel

    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: session
    try:
        client = TestClient(app)

        # Public GET (enabled)
        res_pub = client.get("/api/v1/public/instagram-reels")
        assert res_pub.status_code == status.HTTP_200_OK
        pub_data = res_pub.json()["data"]
        assert pub_data["is_enabled"] is True
        assert len(pub_data["items"]) == 1
        assert set(pub_data["items"][0].keys()) == {
            "id",
            "title",
            "instagram_url",
            "embed_url",
            "description",
            "display_order",
        }

        # Admin GET settings (ensures /settings isn't shadowed by /{id})
        res_get_settings = client.get("/api/v1/admin/instagram-reels/settings")
        assert res_get_settings.status_code == status.HTTP_200_OK
        assert res_get_settings.json()["data"]["is_enabled"] is True

        # Admin PUT settings (disable)
        res_put_settings = client.put(
            "/api/v1/admin/instagram-reels/settings", json={"is_enabled": False}
        )
        assert res_put_settings.status_code == status.HTTP_200_OK
        assert res_put_settings.json()["data"]["is_enabled"] is False

        # Public GET (now disabled)
        res_pub_disabled = client.get("/api/v1/public/instagram-reels")
        assert res_pub_disabled.status_code == status.HTTP_200_OK
        assert res_pub_disabled.json()["data"] == {
            "is_enabled": False,
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "total_pages": 0,
        }

        # Admin POST create
        res_create = client.post(
            "/api/v1/admin/instagram-reels",
            json={
                "title": "New Villa Reel",
                "instagram_url": "https://www.instagram.com/reel/Abcd1234/",
                "description": "Walkthrough",
                "is_published": True,
                "display_order": 0,
            },
        )
        assert res_create.status_code == status.HTTP_201_CREATED
        assert (
            res_create.json()["data"]["embed_url"]
            == "https://www.instagram.com/reel/Abcd1234/embed/"
        )

        # Admin GET list & detail
        assert client.get("/api/v1/admin/instagram-reels").status_code == status.HTTP_200_OK
        assert client.get("/api/v1/admin/instagram-reels/7").status_code == status.HTTP_200_OK

        # Admin PUT update
        res_update = client.put(
            "/api/v1/admin/instagram-reels/7",
            json={"title": "Updated Reel Title"},
        )
        assert res_update.status_code == status.HTTP_200_OK
        assert res_update.json()["data"]["title"] == "Updated Reel Title"

        # Admin PATCH publish & order
        res_patch_pub = client.patch(
            "/api/v1/admin/instagram-reels/7/publish", json={"is_published": False}
        )
        assert res_patch_pub.status_code == status.HTTP_200_OK
        assert res_patch_pub.json()["data"]["is_published"] is False

        res_patch_order = client.patch(
            "/api/v1/admin/instagram-reels/7/order", json={"display_order": 4}
        )
        assert res_patch_order.status_code == status.HTTP_200_OK
        assert res_patch_order.json()["data"]["display_order"] == 4

        # Admin DELETE
        res_del = client.delete("/api/v1/admin/instagram-reels/7")
        assert res_del.status_code == status.HTTP_204_NO_CONTENT
    finally:
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_db, None)
