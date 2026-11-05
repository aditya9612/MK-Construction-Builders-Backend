"""Website CMS services. Separate from ERP models and construction job projects."""

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.cms_enums import PublicationStatus
from app.models.enums import TimestampMixin


class WebsiteService(TimestampMixin, Base):
    """Public website service card — never reuse ERP tables."""

    __tablename__ = "website_services"
    __table_args__ = (UniqueConstraint("slug", name="uq_website_services_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    image_id: Mapped[int] = mapped_column(
        ForeignKey("uploaded_media.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    publication_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PublicationStatus.DRAFT.value,
        index=True,
    )

    image: Mapped["UploadedMedia"] = relationship(
        back_populates="website_services",
        foreign_keys=[image_id],
    )


from app.models.uploaded_media import UploadedMedia  # noqa: F401,E402
