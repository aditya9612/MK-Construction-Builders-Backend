from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TimestampMixin


class CompanySettings(TimestampMixin, Base):
    __tablename__ = "company_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    quotation_prefix: Mapped[str] = mapped_column(String(20), nullable=False, default="MKQ")
    default_gst: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=Decimal("18.00"))
    bank_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signature_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
