import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.audit import AuditLog

logger = get_logger(__name__)


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        *,
        user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: int | None,
        old_data: Any = None,
        new_data: Any = None,
    ) -> None:
        record = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=json.dumps(old_data, default=str) if old_data is not None else None,
            new_data=json.dumps(new_data, default=str) if new_data is not None else None,
        )
        self.session.add(record)
        logger.info("audit %s %s id=%s", action, entity_type, entity_id)
