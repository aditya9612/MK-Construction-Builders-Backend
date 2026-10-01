from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_write
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerUpdate
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post(
    "",
    response_model=SuccessResponse[CustomerOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_write),
):
    data = await CustomerService(db).create(payload)
    return SuccessResponse(message="Customer created successfully", data=data)


@router.get(
    "",
    response_model=SuccessResponse[PaginatedData[CustomerOut]],
    summary="List customers",
)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = await CustomerService(db).list(
        page=page,
        page_size=page_size,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@router.get("/{customer_id}", response_model=SuccessResponse[CustomerOut], summary="Get customer")
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await CustomerService(db).get(customer_id))


@router.put("/{customer_id}", response_model=SuccessResponse[CustomerOut], summary="Update customer")
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_write),
):
    data = await CustomerService(db).update(customer_id, payload)
    return SuccessResponse(message="Customer updated successfully", data=data)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate customer",
    description="Soft-deletes a customer by setting is_active=false.",
)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_write),
):
    await CustomerService(db).delete(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
