from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TimestampMixin


class Quotation(TimestampMixin, Base):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_number: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quotation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0.00"))
    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    gst_percentage: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("18.00")
    )
    gst_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="quotations")
    project: Mapped["Project"] = relationship(back_populates="quotations")
    creator: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    updater: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    construction_items: Mapped[list["QuotationConstructionItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    additional_items: Mapped[list["QuotationAdditionalItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    electrical_items: Mapped[list["QuotationElectricalItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    plumbing_items: Mapped[list["QuotationPlumbingItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    doors: Mapped[list["QuotationDoor"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    windows: Mapped[list["QuotationWindow"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    tiles: Mapped[list["QuotationTile"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    granite: Mapped[list["QuotationGranite"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    painting: Mapped[list["QuotationPainting"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    materials: Mapped[list["QuotationMaterial"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    terms: Mapped[list["QuotationTerm"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
