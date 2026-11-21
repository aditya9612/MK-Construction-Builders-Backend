"""Website enquiry leads from the public enquiry form."""

from sqlalchemy import Boolean, Index, Integer, String, Text

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.cms_enums import EnquiryStatus
from app.models.enums import TimestampMixin


class WebsiteEnquiry(TimestampMixin, Base):
    """Public website enquiry — never reuse ERP customers/quotations tables."""

    __tablename__ = "website_enquiries"
    __table_args__ = (
        Index("ix_website_enquiries_is_read_created_at", "is_read", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    mobile: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    project_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    construction_area: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=EnquiryStatus.NEW.value,
        index=True,
    )
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="WEBSITE")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
