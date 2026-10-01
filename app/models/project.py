from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TimestampMixin


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    site_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    plot_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    construction_area: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    number_of_floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    floor_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PLANNING", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="projects")
    quotations: Mapped[list["Quotation"]] = relationship(back_populates="project")
