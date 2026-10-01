import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate
from app.schemas.quotation import QuotationCreate
from app.utils.validators import validate_indian_mobile


def test_valid_mobile():
    assert validate_indian_mobile("9845098765") == "9845098765"
    assert validate_indian_mobile("+91 9845098765") == "9845098765"


def test_invalid_mobile():
    with pytest.raises(ValueError):
        validate_indian_mobile("12345")


def test_customer_requires_name_and_mobile():
    with pytest.raises(ValidationError):
        CustomerCreate(name="", mobile="9845098765")
    with pytest.raises(ValidationError):
        CustomerCreate(name="Ramesh", mobile="111")


def test_negative_quantity_rejected():
    with pytest.raises(ValidationError):
        QuotationCreate.model_validate(
            {
                "customer_id": 1,
                "project_id": 1,
                "quotation_date": "2026-09-10",
                "construction_items": [
                    {"description": "Foundation", "quantity": -1, "rate": 900}
                ],
            }
        )


def test_discount_over_100_rejected():
    with pytest.raises(ValidationError):
        QuotationCreate.model_validate(
            {
                "customer_id": 1,
                "project_id": 1,
                "quotation_date": "2026-09-10",
                "discount_percentage": 120,
            }
        )
