from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.schemas.common import PaginatedData
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.utils.pagination import paginate
from app.utils.quotation_number import generate_coded_number


class CustomerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CustomerRepository(session)

    async def create(self, payload: CustomerCreate) -> CustomerOut:
        code = await generate_coded_number(self.session, Customer, "customer_code", "MKC")
        customer = Customer(customer_code=code, **payload.model_dump())
        await self.repo.add(customer)
        await self.session.commit()
        await self.session.refresh(customer)
        return CustomerOut.model_validate(customer)

    async def get(self, customer_id: int) -> CustomerOut:
        customer = await self.repo.get(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        return CustomerOut.model_validate(customer)

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        is_active: bool | None,
        sort_by: str,
        sort_order: str,
    ) -> PaginatedData[CustomerOut]:
        items, data = await paginate(
            self.session,
            self.repo.list_query(search, is_active, sort_by, sort_order),
            page,
            page_size,
        )
        return PaginatedData(
            items=[CustomerOut.model_validate(item) for item in items],
            total=data.total,
            page=data.page,
            page_size=data.page_size,
            total_pages=data.total_pages,
        )

    async def update(self, customer_id: int, payload: CustomerUpdate) -> CustomerOut:
        customer = await self.repo.get(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(customer, key, value)
        await self.session.commit()
        await self.session.refresh(customer)
        return CustomerOut.model_validate(customer)

    async def delete(self, customer_id: int) -> None:
        customer = await self.repo.get(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        customer.is_active = False
        await self.session.commit()
