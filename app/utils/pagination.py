from math import ceil

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.common import PaginatedData


async def paginate(
    session: AsyncSession,
    query: Select,
    page: int,
    page_size: int,
) -> tuple[list, PaginatedData]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    count_stmt = select(func.count()).select_from(query.order_by(None).subquery())
    total = int((await session.execute(count_stmt)).scalar_one())
    offset = (page - 1) * page_size
    result = await session.execute(query.offset(offset).limit(page_size))
    items = list(result.unique().scalars().all())
    total_pages = ceil(total / page_size) if page_size else 0
    return items, PaginatedData(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
