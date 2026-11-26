"""add instagram reels and section settings

Revision ID: 9a4d2e6f8b10
Revises: 5e8a1c9b2f34, 7f3a8c1b4d20
Create Date: 2026-11-26 23:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a4d2e6f8b10"
down_revision: Union[str, Sequence[str], None] = "890aaaefab39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "instagram_reels",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instagram_url", sa.String(length=500), nullable=False),
        sa.Column("embed_url", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("display_order >= 0", name="ck_instagram_reels_display_order"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_instagram_reels_title"), "instagram_reels", ["title"], unique=False)
    op.create_index(
        op.f("ix_instagram_reels_is_published"), "instagram_reels", ["is_published"], unique=False
    )
    op.create_index(
        op.f("ix_instagram_reels_display_order"),
        "instagram_reels",
        ["display_order"],
        unique=False,
    )
    op.create_index(
        "ix_instagram_reels_pub_order",
        "instagram_reels",
        ["is_published", "display_order"],
        unique=False,
    )

    op.create_table(
        "instagram_section_settings",
        sa.Column("id", sa.Integer(), autoincrement=False, server_default=sa.text("1"), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_instagram_section_settings_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )

    settings_table = sa.table(
        "instagram_section_settings",
        sa.column("id", sa.Integer()),
        sa.column("is_enabled", sa.Boolean()),
    )
    op.bulk_insert(
        settings_table,
        [{"id": 1, "is_enabled": True}],
    )


def downgrade() -> None:
    op.drop_table("instagram_section_settings")
    op.drop_index("ix_instagram_reels_pub_order", table_name="instagram_reels")
    op.drop_index(op.f("ix_instagram_reels_display_order"), table_name="instagram_reels")
    op.drop_index(op.f("ix_instagram_reels_is_published"), table_name="instagram_reels")
    op.drop_index(op.f("ix_instagram_reels_title"), table_name="instagram_reels")
    op.drop_table("instagram_reels")
