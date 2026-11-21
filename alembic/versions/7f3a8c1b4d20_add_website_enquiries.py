"""add website enquiries

Revision ID: 7f3a8c1b4d20
Revises: 4b7c1d9e2a10
Create Date: 2026-11-21 17:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f3a8c1b4d20"
down_revision: Union[str, None] = "4b7c1d9e2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "website_enquiries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("mobile", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("project_type", sa.String(length=120), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("construction_area", sa.String(length=120), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_website_enquiries_name"), "website_enquiries", ["name"], unique=False)
    op.create_index(op.f("ix_website_enquiries_mobile"), "website_enquiries", ["mobile"], unique=False)
    op.create_index(op.f("ix_website_enquiries_email"), "website_enquiries", ["email"], unique=False)
    op.create_index(op.f("ix_website_enquiries_status"), "website_enquiries", ["status"], unique=False)
    op.create_index(op.f("ix_website_enquiries_is_read"), "website_enquiries", ["is_read"], unique=False)
    op.create_index(op.f("ix_website_enquiries_created_at"), "website_enquiries", ["created_at"], unique=False)
    op.create_index(
        "ix_website_enquiries_is_read_created_at",
        "website_enquiries",
        ["is_read", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_website_enquiries_is_read_created_at", table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_created_at"), table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_is_read"), table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_status"), table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_email"), table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_mobile"), table_name="website_enquiries")
    op.drop_index(op.f("ix_website_enquiries_name"), table_name="website_enquiries")
    op.drop_table("website_enquiries")
