"""Complete customer records with addresses, contacts, and history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_customer_management"
down_revision: str | None = "0003_role_permissions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("legal_form", sa.String(100), nullable=True))
    op.add_column("customers", sa.Column("vat_number", sa.String(32), nullable=True))
    op.add_column("customers", sa.Column("tax_number", sa.String(32), nullable=True))
    op.add_column("customers", sa.Column("internal_notes", sa.Text(), nullable=True))
    op.add_column(
        "customers",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_customers_status_archived",
        "customers",
        ["status", "archived_at"],
    )
    op.create_table(
        "customer_addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("street", sa.String(160), nullable=False),
        sa.Column("house_number", sa.String(30), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="DE"),
        sa.UniqueConstraint("customer_id", "kind", name="uq_customer_addresses_customer_kind"),
        sa.CheckConstraint(
            "kind IN ('business', 'billing')",
            name="ck_customer_addresses_kind",
        ),
        sa.CheckConstraint(
            "length(trim(street)) > 0 AND length(trim(city)) > 0",
            name="ck_customer_addresses_required_fields",
        ),
    )
    op.create_table(
        "customer_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("responsibility", sa.String(120), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(
            "length(trim(first_name)) > 0 AND length(trim(last_name)) > 0",
            name="ck_customer_contacts_name",
        ),
    )
    op.create_index(
        "ix_customer_contacts_customer_name",
        "customer_contacts",
        ["customer_id", "last_name", "first_name"],
    )
    op.create_index(
        "uq_customer_contacts_primary",
        "customer_contacts",
        ["customer_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_table(
        "customer_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
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
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_customer_history_customer_created",
        "customer_history",
        ["customer_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_customer_history_customer_created", table_name="customer_history")
    op.drop_table("customer_history")
    op.drop_index("uq_customer_contacts_primary", table_name="customer_contacts")
    op.drop_index("ix_customer_contacts_customer_name", table_name="customer_contacts")
    op.drop_table("customer_contacts")
    op.drop_table("customer_addresses")
    op.drop_index("ix_customers_status_archived", table_name="customers")
    op.drop_column("customers", "archived_at")
    op.drop_column("customers", "internal_notes")
    op.drop_column("customers", "tax_number")
    op.drop_column("customers", "vat_number")
    op.drop_column("customers", "legal_form")
