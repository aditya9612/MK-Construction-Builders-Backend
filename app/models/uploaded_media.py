"""Website CMS media metadata. Separate from any ERP models."""

from sqlalchemy import BigInteger, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.cms_enums import MediaFolder
from app.models.enums import TimestampMixin


class UploadedMedia(TimestampMixin, Base):
    """Durable storage reference for uploaded website images.

    Files live under a configured MEDIA_ROOT (intended for a persistent volume).
    Container-local paths alone are not assumed durable.
    """

    __tablename__ = "uploaded_media"
    __table_args__ = (UniqueConstraint("storage_key", name="uq_uploaded_media_storage_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    folder: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        default=MediaFolder.GALLERY.value,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    portfolio_as_main: Mapped[list["PortfolioProject"]] = relationship(
        back_populates="main_image",
        foreign_keys="PortfolioProject.main_image_id",
    )
    gallery_items: Mapped[list["GalleryItem"]] = relationship(back_populates="media")
    portfolio_gallery_links: Mapped[list["PortfolioProjectGallery"]] = relationship(
        back_populates="media",
    )


# Ensure related CMS models are registered in SQLAlchemy mapper registry
from app.models.gallery_item import GalleryItem  # noqa: F401,E402
from app.models.portfolio_gallery import PortfolioProjectGallery  # noqa: F401,E402
from app.models.portfolio_project import PortfolioProject  # noqa: F401,E402


