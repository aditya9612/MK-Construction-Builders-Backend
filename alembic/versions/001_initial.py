"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-09-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("customer_code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("mobile", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("customer_type", sa.String(length=30), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("pincode", sa.String(length=10), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("customer_code"),
    )
    op.create_index("ix_customers_name", "customers", ["name"])
    op.create_index("ix_customers_mobile", "customers", ["mobile"])
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_is_active", "customers", ["is_active"])

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_code", sa.String(length=30), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("project_name", sa.String(length=200), nullable=False),
        sa.Column("site_address", sa.Text(), nullable=True),
        sa.Column("plot_area", sa.Numeric(12, 2), nullable=True),
        sa.Column("construction_area", sa.Numeric(12, 2), nullable=True),
        sa.Column("number_of_floors", sa.Integer(), nullable=True),
        sa.Column("floor_type", sa.String(length=50), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_code"),
    )
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"])
    op.create_index("ix_projects_project_name", "projects", ["project_name"])
    op.create_index("ix_projects_status", "projects", ["status"])

    def master_table(name: str) -> None:
        op.create_table(
            name,
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("category", sa.String(length=50), nullable=False),
            sa.Column("unit", sa.String(length=30), nullable=False),
            sa.Column("rate", sa.Numeric(15, 2), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    op.create_table(
        "rate_master",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rate_master_category", "rate_master", ["category"])
    op.create_index("ix_rate_master_is_active", "rate_master", ["is_active"])

    op.create_table(
        "material_master",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("specification", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_master_category", "material_master", ["category"])
    op.create_index("ix_material_master_is_active", "material_master", ["is_active"])

    for table in (
        "electrical_master",
        "plumbing_master",
        "door_window_master",
        "tile_granite_master",
        "painting_master",
    ):
        master_table(table)

    op.create_table(
        "terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "company_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("mobile", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("gst_number", sa.String(length=30), nullable=True),
        sa.Column("quotation_prefix", sa.String(length=20), nullable=False),
        sa.Column("default_gst", sa.Numeric(6, 2), nullable=False),
        sa.Column("bank_name", sa.String(length=150), nullable=True),
        sa.Column("account_number", sa.String(length=50), nullable=True),
        sa.Column("ifsc_code", sa.String(length=20), nullable=True),
        sa.Column("signature_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_number", sa.String(length=40), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("quotation_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("subtotal", sa.Numeric(15, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(6, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("gst_percentage", sa.Numeric(6, 2), nullable=False),
        sa.Column("gst_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("grand_total", sa.Numeric(15, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quotation_number"),
    )
    op.create_index("ix_quotations_customer_id", "quotations", ["customer_id"])
    op.create_index("ix_quotations_project_id", "quotations", ["project_id"])
    op.create_index("ix_quotations_quotation_date", "quotations", ["quotation_date"])
    op.create_index("ix_quotations_status", "quotations", ["status"])
    op.create_index("ix_quotations_created_at", "quotations", ["created_at"])

    op.create_table(
        "quotation_construction_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("rate_master_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rate_master_id"], ["rate_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qci_quotation_id", "quotation_construction_items", ["quotation_id"])

    op.create_table(
        "quotation_additional_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qai_quotation_id", "quotation_additional_items", ["quotation_id"])

    op.create_table(
        "quotation_electrical_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("area", sa.String(length=100), nullable=True),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qei_quotation_id", "quotation_electrical_items", ["quotation_id"])

    op.create_table(
        "quotation_plumbing_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qpi_quotation_id", "quotation_plumbing_items", ["quotation_id"])

    op.create_table(
        "quotation_doors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["door_window_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qd_quotation_id", "quotation_doors", ["quotation_id"])

    op.create_table(
        "quotation_windows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("length", sa.Numeric(12, 2), nullable=False),
        sa.Column("width", sa.Numeric(12, 2), nullable=False),
        sa.Column("area", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["door_window_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qw_quotation_id", "quotation_windows", ["quotation_id"])

    op.create_table(
        "quotation_tiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("area", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["tile_granite_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qt_quotation_id", "quotation_tiles", ["quotation_id"])

    op.create_table(
        "quotation_granite",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("area", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["tile_granite_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qg_quotation_id", "quotation_granite", ["quotation_id"])

    op.create_table(
        "quotation_painting",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("area", sa.Numeric(15, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("rate", sa.Numeric(15, 2), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qp_quotation_id", "quotation_painting", ["quotation_id"])

    op.create_table(
        "quotation_materials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=True),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("specification", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["material_master.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qm_quotation_id", "quotation_materials", ["quotation_id"])

    op.create_table(
        "quotation_terms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), nullable=False),
        sa.Column("term_id", sa.Integer(), nullable=True),
        sa.Column("term_order", sa.Integer(), nullable=False),
        sa.Column("custom_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["quotation_id"], ["quotations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["term_id"], ["terms.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_qterms_quotation_id", "quotation_terms", ["quotation_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("old_data", sa.Text(), nullable=True),
        sa.Column("new_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("quotation_terms")
    op.drop_table("quotation_materials")
    op.drop_table("quotation_painting")
    op.drop_table("quotation_granite")
    op.drop_table("quotation_tiles")
    op.drop_table("quotation_windows")
    op.drop_table("quotation_doors")
    op.drop_table("quotation_plumbing_items")
    op.drop_table("quotation_electrical_items")
    op.drop_table("quotation_additional_items")
    op.drop_table("quotation_construction_items")
    op.drop_table("quotations")
    op.drop_table("company_settings")
    op.drop_table("terms")
    op.drop_table("painting_master")
    op.drop_table("tile_granite_master")
    op.drop_table("door_window_master")
    op.drop_table("plumbing_master")
    op.drop_table("electrical_master")
    op.drop_table("material_master")
    op.drop_table("rate_master")
    op.drop_table("projects")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("roles")
