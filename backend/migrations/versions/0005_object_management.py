"""Add object management tables with customer linkage and history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_object_management"
down_revision: str | None = "0004_customer_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("object_type", sa.String(120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("operating_hours", sa.String(200), nullable=True),
        sa.Column("service_times", sa.String(200), nullable=True),
        sa.Column("security_requirements", sa.Text(), nullable=True),
        sa.Column("staffing_requirements", sa.Text(), nullable=True),
        sa.Column("access_information", sa.Text(), nullable=True),
        sa.Column("emergency_contact", sa.String(200), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_objects_status"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_objects_name"),
        sa.CheckConstraint("length(trim(code)) > 0", name="ck_objects_code"),
    )
    op.create_index(
        "ix_objects_customer_status", "objects", ["customer_id", "status", "archived_at"]
    )
    op.create_index("ix_objects_code", "objects", ["code"], unique=True)

    op.create_table(
        "object_addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("street", sa.String(160), nullable=False),
        sa.Column("house_number", sa.String(30), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="DE"),
        sa.CheckConstraint(
            "length(trim(street)) > 0 AND length(trim(city)) > 0",
            name="ck_object_addresses_required_fields",
        ),
    )

    op.create_table(
        "object_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(120), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(
            "length(trim(first_name)) > 0 AND length(trim(last_name)) > 0",
            name="ck_object_contacts_name",
        ),
    )
    op.create_index(
        "ix_object_contacts_object_name",
        "object_contacts",
        ["object_id", "last_name", "first_name"],
    )
    op.create_index(
        "uq_object_contacts_primary",
        "object_contacts",
        ["object_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )

    op.create_table(
        "object_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_object_history_object_created", "object_history", ["object_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_object_history_object_created", table_name="object_history")
    op.drop_table("object_history")
    op.drop_index("uq_object_contacts_primary", table_name="object_contacts")
    op.drop_index("ix_object_contacts_object_name", table_name="object_contacts")
    op.drop_table("object_contacts")
    op.drop_table("object_addresses")
    op.drop_index("ix_objects_code", table_name="objects")
    op.drop_index("ix_objects_customer_status", table_name="objects")
    op.drop_table("objects")
