"""Website gallery items. Separate from ERP models and portfolio projects."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.cms_enums import GalleryCategory, PublicationStatus
from app.models.enums import TimestampMixin


class GalleryItem(TimestampMixin, Base):
    """Standalone website gallery entry with media reference and display metadata."""

    __tablename__ = "gallery_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    media_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_media.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    caption: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=GalleryCategory.OTHER.value,
        index=True,
    )
    object_position: Mapped[str] = mapped_column(String(50), nullable=False, default="center")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    publication_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PublicationStatus.DRAFT.value,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    media: Mapped["UploadedMedia"] = relationship(back_populates="gallery_items")


# Ensure related CMS models are registered in SQLAlchemy mapper registry
from app.models.uploaded_media import UploadedMedia  # noqa: F401,E402


