from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleName
from app.api.deps import APPROVE_ROLES, MASTER_ROLES, SETTINGS_ROLES, WRITE_ROLES, _user_role


def test_password_hash_roundtrip():
    hashed = hash_password("Admin@12345")
    assert hashed != "Admin@12345"
    assert verify_password("Admin@12345", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_types():
    access = create_access_token("1")
    refresh = create_refresh_token("1")
    assert decode_token(access, "access")["sub"] == "1"
    assert decode_token(refresh, "refresh")["sub"] == "1"


def test_rbac_sets():
    assert RoleName.ADMIN in WRITE_ROLES
    assert RoleName.VIEWER not in WRITE_ROLES
    assert RoleName.ESTIMATOR in WRITE_ROLES
    assert RoleName.ESTIMATOR not in MASTER_ROLES
    assert RoleName.ESTIMATOR not in APPROVE_ROLES
    assert RoleName.MANAGER in APPROVE_ROLES
    assert RoleName.ADMIN in SETTINGS_ROLES
    assert RoleName.VIEWER not in SETTINGS_ROLES
    assert RoleName.MANAGER not in SETTINGS_ROLES
    assert RoleName.ESTIMATOR not in SETTINGS_ROLES


class _FakeRole:
    def __init__(self, name):
        self.name = name


class _FakeUser:
    def __init__(self, name):
        self.role = _FakeRole(name)


def test_user_role_normalizes_viewer_and_rejects_unknown():
    assert _user_role(_FakeUser("VIEWER")) == RoleName.VIEWER
    assert _user_role(_FakeUser("viewer")) == RoleName.VIEWER
    assert _user_role(_FakeUser("ADMIN")) == RoleName.ADMIN

    from app.core.exceptions import ForbiddenError

    try:
        _user_role(_FakeUser("not-a-role"))
        raise AssertionError("expected ForbiddenError")
    except ForbiddenError:
        pass
