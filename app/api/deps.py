from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.models.enums import RoleName
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

WRITE_ROLES = {RoleName.ADMIN, RoleName.MANAGER, RoleName.ESTIMATOR}
MASTER_ROLES = {RoleName.ADMIN, RoleName.MANAGER}
APPROVE_ROLES = {RoleName.ADMIN, RoleName.MANAGER}
SETTINGS_ROLES = {RoleName.ADMIN}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedError("Missing authorization token")
    try:
        payload = decode_token(credentials.credentials, "access")
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    user = (
        await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == int(payload["sub"]))
        )
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid or expired token")
    return user


def require_roles(*roles: RoleName) -> Callable:
    allowed = set(roles)

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role.name not in allowed and user.role.name != RoleName.ADMIN:
            raise ForbiddenError("You do not have permission to perform this action")
        return user

    return _checker


async def require_write(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in WRITE_ROLES:
        raise ForbiddenError("Read-only users cannot modify data")
    return user


async def require_masters(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in MASTER_ROLES:
        raise ForbiddenError("Master data can only be changed by managers")
    return user


async def require_approve(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in APPROVE_ROLES:
        raise ForbiddenError("Only managers can change quotation status")
    return user


async def require_settings(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in SETTINGS_ROLES:
        raise ForbiddenError("Only administrators can change company settings")
    return user
