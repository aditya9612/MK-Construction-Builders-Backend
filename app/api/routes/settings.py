from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.company import CompanySettingsOut, CompanySettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/company", response_model=SuccessResponse[CompanySettingsOut], summary="Get company settings")
async def get_company(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await SettingsService(db).get())


@router.put("/company", response_model=SuccessResponse[CompanySettingsOut], summary="Update company settings")
async def update_company(
    payload: CompanySettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_settings),
):
    return SuccessResponse(
        message="Company settings updated",
        data=await SettingsService(db).update(payload, user),
    )
