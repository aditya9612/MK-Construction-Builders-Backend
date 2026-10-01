from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.company import CompanySettings
from app.models.user import User
from app.schemas.company import CompanySettingsOut, CompanySettingsUpdate
from app.services.audit_service import AuditService


class SettingsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit = AuditService(session)

    async def get(self) -> CompanySettingsOut:
        company = (await self.session.execute(select(CompanySettings).limit(1))).scalar_one_or_none()
        if not company:
            raise NotFoundError("Company settings not found")
        return CompanySettingsOut.model_validate(company)

    async def update(self, payload: CompanySettingsUpdate, user: User) -> CompanySettingsOut:
        company = (await self.session.execute(select(CompanySettings).limit(1))).scalar_one_or_none()
        if not company:
            raise NotFoundError("Company settings not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(company, key, value)
        await self.audit.log(
            user_id=user.id,
            action="company_settings.changed",
            entity_type="company_settings",
            entity_id=company.id,
            new_data=payload.model_dump(exclude_unset=True),
        )
        await self.session.commit()
        await self.session.refresh(company)
        return CompanySettingsOut.model_validate(company)
