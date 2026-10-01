from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import CustomerType
from app.schemas.common import ORMModel
from app.utils.validators import validate_indian_mobile


class CustomerBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    mobile: str
    email: EmailStr | None = None
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    pincode: str | None = Field(default=None, max_length=10)
    notes: str | None = None
    is_active: bool = True

    @field_validator("mobile")
    @classmethod
    def mobile_ok(cls, value: str) -> str:
        return validate_indian_mobile(value)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    mobile: str | None = None
    email: EmailStr | None = None
    customer_type: CustomerType | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("mobile")
    @classmethod
    def mobile_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_indian_mobile(value)


class CustomerOut(ORMModel):
    id: int
    customer_code: str
    name: str
    mobile: str
    email: str | None
    customer_type: str
    address: str | None
    city: str | None
    state: str | None
    pincode: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
