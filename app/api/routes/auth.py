from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=SuccessResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Register user",
    description="Creates a new user. The first user becomes ADMIN; later users default to VIEWER.",
)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService(db).register(payload)
    return SuccessResponse(message="User registered successfully", data=UserOut.model_validate(user))


@router.post(
    "/login",
    response_model=SuccessResponse[TokenResponse],
    summary="Login",
    description="Authenticate with email and password and receive JWT tokens.",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).login(payload)
    return SuccessResponse(message="Login successful", data=tokens)


@router.post(
    "/refresh",
    response_model=SuccessResponse[TokenResponse],
    summary="Refresh access token",
    description="Issue a new access token using a valid refresh token.",
)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    tokens = await AuthService(db).refresh(payload.refresh_token)
    return SuccessResponse(message="Token refreshed", data=tokens)


@router.get(
    "/me",
    response_model=SuccessResponse[UserOut],
    summary="Current user",
    description="Return the authenticated user profile.",
)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await AuthService(db).me(user)
    return SuccessResponse(data=data)
