from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, customer_id: int) -> Customer | None:
        return await self.session.get(Customer, customer_id)

    def list_query(
        self,
        search: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Select:
        stmt = select(Customer)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Customer.name.ilike(like),
                    Customer.mobile.ilike(like),
                    Customer.email.ilike(like),
                    Customer.customer_code.ilike(like),
                )
            )
        if is_active is not None:
            stmt = stmt.where(Customer.is_active.is_(is_active))
        column = getattr(Customer, sort_by, Customer.created_at)
        stmt = stmt.order_by(column.asc() if sort_order == "asc" else column.desc())
        return stmt

    async def add(self, customer: Customer) -> Customer:
        self.session.add(customer)
        await self.session.flush()
        return customer
