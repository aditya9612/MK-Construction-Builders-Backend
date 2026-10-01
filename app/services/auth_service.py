from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.enums import RoleName
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _role_by_name(self, name: str) -> Role:
        role = (await self.session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
        if not role:
            raise NotFoundError(f"Role {name} is not configured")
        return role

    async def register(self, payload: RegisterRequest) -> User:
        existing = await self.get_user_by_email(payload.email)
        if existing:
            raise ConflictError("Email is already registered")
        user_count = (await self.session.execute(select(func.count(User.id)))).scalar_one()
        role_name = RoleName.ADMIN if user_count == 0 else RoleName.VIEWER
        role = await self._role_by_name(role_name)
        user = User(
            name=payload.name,
            email=str(payload.email).lower(),
            phone=payload.phone,
            password_hash=hash_password(payload.password),
            role_id=role.id,
            is_active=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user, attribute_names=["role"])
        return user

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.get_user_by_email(str(payload.email).lower())
        if not user or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise ForbiddenError("User is inactive")
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, "refresh")
        except ValueError as exc:
            raise UnauthorizedError("Invalid refresh token") from exc
        user = await self.get_user_by_id(int(payload["sub"]))
        if not user or not user.is_active:
            raise UnauthorizedError("Invalid refresh token")
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def me(self, user: User) -> UserOut:
        await self.session.refresh(user, attribute_names=["role"])
        return UserOut.model_validate(user)
