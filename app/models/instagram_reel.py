"""Instagram Reels and section settings database models."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TimestampMixin


class InstagramReel(TimestampMixin, Base):
    """Instagram Reel showcase entry managed by CMS administrators."""

    __tablename__ = "instagram_reels"
    __table_args__ = (
        CheckConstraint("display_order >= 0", name="ck_instagram_reels_display_order"),
        Index("ix_instagram_reels_pub_order", "is_published", "display_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    instagram_url: Mapped[str] = mapped_column(String(500), nullable=False)
    embed_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0"),
        index=True,
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        index=True,
    )


class InstagramSectionSettings(Base):
    """Singleton settings controlling public visibility of the Instagram Reels section.

    Singleton constraint is enforced at the database level via ``id = 1`` as primary
    key (non-autoincrement) combined with a CHECK constraint ``id = 1``.
    """

    __tablename__ = "instagram_section_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_instagram_section_settings_singleton"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=False,
        default=1,
        server_default=text("1"),
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
