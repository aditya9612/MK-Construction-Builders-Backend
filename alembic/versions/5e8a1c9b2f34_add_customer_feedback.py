"""add customer feedback table

Revision ID: 5e8a1c9b2f34
Revises: 4b7c1d9e2a10
Create Date: 2026-11-20 15:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5e8a1c9b2f34"
down_revision: Union[str, None] = "4b7c1d9e2a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("customer_location", sa.String(length=150), nullable=False),
        sa.Column("customer_photo", sa.String(length=500), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_title", sa.String(length=200), nullable=True),
        sa.Column("review_message", sa.Text(), nullable=False),
        sa.Column("project_name", sa.String(length=200), nullable=True),
        sa.Column("review_source", sa.String(length=20), server_default="website", nullable=False),
        sa.Column("google_review_url", sa.String(length=500), nullable=True),
        sa.Column("review_date", sa.Date(), server_default=sa.text("(CURRENT_DATE)"), nullable=False),
        sa.Column("is_featured", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_customer_feedback_rating"),
        sa.CheckConstraint("review_source IN ('google', 'website', 'manual')", name="ck_customer_feedback_review_source"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customer_feedback_customer_name"), "customer_feedback", ["customer_name"], unique=False)
    op.create_index(op.f("ix_customer_feedback_rating"), "customer_feedback", ["rating"], unique=False)
    op.create_index(op.f("ix_customer_feedback_review_source"), "customer_feedback", ["review_source"], unique=False)
    op.create_index(op.f("ix_customer_feedback_review_date"), "customer_feedback", ["review_date"], unique=False)
    op.create_index(op.f("ix_customer_feedback_is_featured"), "customer_feedback", ["is_featured"], unique=False)
    op.create_index(op.f("ix_customer_feedback_is_published"), "customer_feedback", ["is_published"], unique=False)
    op.create_index(op.f("ix_customer_feedback_display_order"), "customer_feedback", ["display_order"], unique=False)
    op.create_index("ix_customer_feedback_pub_order", "customer_feedback", ["is_published", "display_order"], unique=False)
    op.create_index("ix_customer_feedback_pub_rating", "customer_feedback", ["is_published", "rating"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_customer_feedback_pub_rating", table_name="customer_feedback")
    op.drop_index("ix_customer_feedback_pub_order", table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_display_order"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_is_published"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_is_featured"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_review_date"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_review_source"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_rating"), table_name="customer_feedback")
    op.drop_index(op.f("ix_customer_feedback_customer_name"), table_name="customer_feedback")
    op.drop_table("customer_feedback")
