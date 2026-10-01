from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hasher.verify(plain_password, password_hash)


def create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": token_type,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    return create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(subject: str) -> str:
    return create_token(
        subject,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type")
    if not payload.get("sub"):
        raise ValueError("Invalid token subject")
    return payload
