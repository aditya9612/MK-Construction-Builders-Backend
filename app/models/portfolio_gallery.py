"""Ordered portfolio project ↔ media relationship for website CMS."""

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TimestampMixin


class PortfolioProjectGallery(TimestampMixin, Base):
    """Join table for portfolio gallery images with stable display ordering."""

    __tablename__ = "portfolio_project_gallery"
    __table_args__ = (
        UniqueConstraint(
            "portfolio_project_id",
            "media_id",
            name="uq_portfolio_project_gallery_project_media",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_project_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_media.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    portfolio_project: Mapped["PortfolioProject"] = relationship(back_populates="gallery_links")
    media: Mapped["UploadedMedia"] = relationship(back_populates="portfolio_gallery_links")


# Ensure related CMS models are registered in SQLAlchemy mapper registry
from app.models.portfolio_project import PortfolioProject  # noqa: F401,E402
from app.models.uploaded_media import UploadedMedia  # noqa: F401,E402


