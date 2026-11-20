"""Customer feedback and Google reviews database model."""

from datetime import date
from enum import StrEnum

from sqlalchemy import Boolean, CheckConstraint, Date, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TimestampMixin


class ReviewSource(StrEnum):
    """Allowed review sources."""

    GOOGLE = "google"
    WEBSITE = "website"
    MANUAL = "manual"


class CustomerFeedback(TimestampMixin, Base):
    """Customer feedback and reviews (Google, Website, Manual)."""

    __tablename__ = "customer_feedback"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_customer_feedback_rating"),
        CheckConstraint(
            "review_source IN ('google', 'website', 'manual')",
            name="ck_customer_feedback_review_source",
        ),
        Index("ix_customer_feedback_pub_order", "is_published", "display_order"),
        Index("ix_customer_feedback_pub_rating", "is_published", "rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    customer_location: Mapped[str] = mapped_column(String(150), nullable=False)
    customer_photo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    review_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    review_message: Mapped[str] = mapped_column(Text, nullable=False)
    project_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    review_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReviewSource.WEBSITE.value,
        index=True,
    )
    google_review_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    review_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=func.current_date(),
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
