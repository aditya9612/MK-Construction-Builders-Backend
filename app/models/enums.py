from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RoleName(StrEnum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ESTIMATOR = "ESTIMATOR"
    VIEWER = "VIEWER"


class CustomerType(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"


class ProjectStatus(StrEnum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"


class QuotationStatus(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class AdditionalCategory(StrEnum):
    WATER_TANK = "WATER_TANK"
    WATERPROOFING = "WATERPROOFING"
    PCC = "PCC"
    RCC = "RCC"
    BRICK_PLASTER = "BRICK_PLASTER"
    OTHER = "OTHER"


class MaterialCategory(StrEnum):
    RCC = "RCC"
    BRICK_PLASTER = "BRICK_PLASTER"
    GRANITE_TILES = "GRANITE_TILES"
    ELECTRICAL = "ELECTRICAL"
    PLUMBING = "PLUMBING"
    DOORS_FRAMES = "DOORS_FRAMES"
    SLIDING = "SLIDING"
    PAINTING = "PAINTING"


class PaintingCategory(StrEnum):
    OUTER = "OUTER"
    INNER = "INNER"


class DoorWindowCategory(StrEnum):
    DOOR = "DOOR"
    WINDOW = "WINDOW"
    FRAME = "FRAME"


class TileGraniteCategory(StrEnum):
    TILE = "TILE"
    GRANITE = "GRANITE"
