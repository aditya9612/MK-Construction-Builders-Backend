"""add website CMS services

Revision ID: 4b7c1d9e2a10
Revises: 3219132a8a91
Create Date: 2026-11-05 19:12:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b7c1d9e2a10"
down_revision: Union[str, None] = "3219132a8a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "website_services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("image_id", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("publication_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["uploaded_media.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_website_services_slug"),
    )
    op.create_index(op.f("ix_website_services_display_order"), "website_services", ["display_order"], unique=False)
    op.create_index(op.f("ix_website_services_image_id"), "website_services", ["image_id"], unique=False)
    op.create_index(op.f("ix_website_services_publication_status"), "website_services", ["publication_status"], unique=False)
    op.create_index(op.f("ix_website_services_slug"), "website_services", ["slug"], unique=False)
    op.create_index(op.f("ix_website_services_title"), "website_services", ["title"], unique=False)


def downgrade() -> None:
    op.drop_table("website_services")
