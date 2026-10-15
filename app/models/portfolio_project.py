"""Website portfolio projects. Separate from ERP ``projects`` / ``Project``."""

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.cms_enums import (
    PortfolioDisplayStatus,
    PortfolioProjectType,
    PublicationStatus,
)
from app.models.enums import TimestampMixin


class PortfolioProject(TimestampMixin, Base):
    """Public website portfolio entry — never reuse ERP Project / projects table."""

    __tablename__ = "portfolio_projects"
    __table_args__ = (UniqueConstraint("slug", name="uq_portfolio_projects_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PortfolioProjectType.RESIDENTIAL.value,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PortfolioDisplayStatus.COMPLETED.value,
        index=True,
    )
    main_image_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploaded_media.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_progress: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PublicationStatus.DRAFT.value,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    main_image: Mapped["UploadedMedia | None"] = relationship(
        back_populates="portfolio_as_main",
        foreign_keys=[main_image_id],
    )
    gallery_links: Mapped[list["PortfolioProjectGallery"]] = relationship(
        back_populates="portfolio_project",
        cascade="all, delete-orphan",
        order_by=lambda: (PortfolioProjectGallery.display_order, PortfolioProjectGallery.id),
    )



# Ensure related CMS models are registered in SQLAlchemy mapper registry
from app.models.portfolio_gallery import PortfolioProjectGallery  # noqa: F401,E402
from app.models.uploaded_media import UploadedMedia  # noqa: F401,E402


