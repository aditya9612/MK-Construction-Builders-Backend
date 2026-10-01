from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TimestampMixin


class QuotationConstructionItem(TimestampMixin, Base):
    __tablename__ = "quotation_construction_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rate_master_id: Mapped[int | None] = mapped_column(
        ForeignKey("rate_master.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="sqft")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="construction_items")


class QuotationAdditionalItem(TimestampMixin, Base):
    __tablename__ = "quotation_additional_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="additional_items")


class QuotationElectricalItem(TimestampMixin, Base):
    __tablename__ = "quotation_electrical_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="nos")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="electrical_items")


class QuotationPlumbingItem(TimestampMixin, Base):
    __tablename__ = "quotation_plumbing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="nos")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="plumbing_items")


class QuotationDoor(TimestampMixin, Base):
    __tablename__ = "quotation_doors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("door_window_master.id", ondelete="SET NULL"), nullable=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="nos")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="doors")


class QuotationWindow(TimestampMixin, Base):
    __tablename__ = "quotation_windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("door_window_master.id", ondelete="SET NULL"), nullable=True
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    length: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    width: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    area: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="sqft")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="windows")


class QuotationTile(TimestampMixin, Base):
    __tablename__ = "quotation_tiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("tile_granite_master.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="TILE")
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="sqft")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="tiles")


class QuotationGranite(TimestampMixin, Base):
    __tablename__ = "quotation_granite"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("tile_granite_master.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="GRANITE")
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="sqft")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="granite")


class QuotationPainting(TimestampMixin, Base):
    __tablename__ = "quotation_painting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="sqft")
    rate: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="painting")


class QuotationMaterial(TimestampMixin, Base):
    __tablename__ = "quotation_materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    material_id: Mapped[int | None] = mapped_column(
        ForeignKey("material_master.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    specification: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="materials")


class QuotationTerm(TimestampMixin, Base):
    __tablename__ = "quotation_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[int | None] = mapped_column(
        ForeignKey("terms.id", ondelete="SET NULL"), nullable=True
    )
    term_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    custom_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    quotation: Mapped["Quotation"] = relationship(back_populates="terms")
    term: Mapped["Term | None"] = relationship()
