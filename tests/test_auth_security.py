from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleName
from app.api.deps import APPROVE_ROLES, MASTER_ROLES, WRITE_ROLES


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
