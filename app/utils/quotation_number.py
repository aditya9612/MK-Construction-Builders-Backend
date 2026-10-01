from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quotation import Quotation


async def generate_quotation_number(
    session: AsyncSession,
    prefix: str = "MKQ",
    year: int | None = None,
) -> str:
    year = year or date.today().year
    pattern = f"{prefix}-{year}-%"
    stmt = (
        select(func.max(Quotation.quotation_number))
        .where(Quotation.quotation_number.like(pattern))
        .with_for_update()
    )
    latest = (await session.execute(stmt)).scalar_one_or_none()
    next_seq = 1
    if latest:
        try:
            next_seq = int(str(latest).rsplit("-", 1)[-1]) + 1
        except ValueError:
            next_seq = 1
    return f"{prefix}-{year}-{next_seq:04d}"


async def generate_coded_number(
    session: AsyncSession,
    model,
    field_name: str,
    prefix: str,
) -> str:
    column = getattr(model, field_name)
    pattern = f"{prefix}-%"
    stmt = select(func.max(column)).where(column.like(pattern)).with_for_update()
    latest = (await session.execute(stmt)).scalar_one_or_none()
    next_seq = 1
    if latest:
        try:
            next_seq = int(str(latest).rsplit("-", 1)[-1]) + 1
        except ValueError:
            next_seq = 1
    return f"{prefix}-{next_seq:04d}"
