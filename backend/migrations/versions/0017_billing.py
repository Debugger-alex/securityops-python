"""Add immutable invoice snapshots, payments, and versioned accounting exports."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0017_billing"
down_revision: str | None = "0016_scheduling_availability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "billing.invoices.read": "Rechnungen und Zahlungsstatus einsehen",
    "billing.invoices.create": "Rechnungsentwürfe und Folgebelege erstellen",
    "billing.invoices.approve": "Rechnungen freigeben",
    "billing.invoices.archive": "Freigegebene Rechnungen archivieren",
    "billing.rates.manage": "Abrechnungspreise konfigurieren",
    "billing.payments.manage": "Zahlungen und Mahnstatus erfassen",
    "billing.exports.create": "Buchhaltungsexporte erzeugen",
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "billing_rates",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("tax_code", sa.String(40), nullable=False),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('hourly', 'flat', 'surcharge')", name="ck_billing_rates_kind"),
        sa.CheckConstraint("unit_price >= 0", name="ck_billing_rates_unit_price"),
        sa.CheckConstraint("tax_rate >= 0 AND tax_rate <= 100", name="ck_billing_rates_tax_rate"),
        sa.UniqueConstraint("code", name="uq_billing_rates_code"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "billing_invoices",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("invoice_number", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("customer_id", uuid, nullable=False),
        sa.Column("contract_id", uuid, nullable=True),
        sa.Column("kind", sa.String(20), nullable=False, server_default="invoice"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("payment_status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("dunning_status", sa.String(20), nullable=False, server_default="none"),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("correction_of_id", uuid, nullable=True),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("customer_snapshot", sa.JSON(), nullable=False),
        sa.Column("inputs_snapshot", sa.JSON(), nullable=False),
        sa.Column("net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gross_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("approved_by_id", uuid, nullable=True),
        sa.Column("approved_at", timestamp, nullable=True),
        sa.Column("archived_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "kind IN ('invoice', 'correction', 'cancellation')", name="ck_billing_invoices_kind"
        ),
        sa.CheckConstraint(
            "(kind = 'invoice' AND correction_of_id IS NULL) OR "
            "(kind IN ('correction', 'cancellation') AND correction_of_id IS NOT NULL)",
            name="ck_billing_invoices_correction_link",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'archived')", name="ck_billing_invoices_status"
        ),
        sa.CheckConstraint(
            "payment_status IN ('open', 'partial', 'paid')",
            name="ck_billing_invoices_payment_status",
        ),
        sa.CheckConstraint(
            "dunning_status IN ('none', 'reminder_1', 'reminder_2', 'final')",
            name="ck_billing_invoices_dunning_status",
        ),
        sa.CheckConstraint("due_on >= issued_on", name="ck_billing_invoices_due_date"),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="ck_billing_invoices_currency",
        ),
        sa.UniqueConstraint("invoice_number", name="uq_billing_invoices_number"),
        sa.UniqueConstraint("idempotency_key", name="uq_billing_invoices_idempotency"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["correction_of_id"], ["billing_invoices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_billing_invoices_customer_date", "billing_invoices", ["customer_id", "issued_on"]
    )
    op.create_index(
        "ix_billing_invoices_status_due",
        "billing_invoices",
        ["status", "payment_status", "due_on"],
    )
    op.create_table(
        "billing_invoice_lines",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("invoice_id", uuid, nullable=False),
        sa.Column("rate_id", uuid, nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("tax_code", sa.String(40), nullable=False),
        sa.Column("tax_rate", sa.Numeric(7, 4), nullable=False),
        sa.Column("net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gross_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("inputs_snapshot", sa.JSON(), nullable=False),
        sa.CheckConstraint("position > 0", name="ck_billing_invoice_lines_position"),
        sa.CheckConstraint(
            "tax_rate >= 0 AND tax_rate <= 100", name="ck_billing_invoice_lines_tax_rate"
        ),
        sa.UniqueConstraint("invoice_id", "position", name="uq_billing_invoice_lines_position"),
        sa.ForeignKeyConstraint(["invoice_id"], ["billing_invoices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["rate_id"], ["billing_rates.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "billing_payments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("invoice_id", uuid, nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("reference", sa.String(160), nullable=True),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_billing_payments_amount"),
        sa.UniqueConstraint(
            "invoice_id", "idempotency_key", name="uq_billing_payments_idempotency"
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["billing_invoices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_billing_payments_invoice_date", "billing_payments", ["invoice_id", "paid_on"]
    )
    op.create_table(
        "billing_exports",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("invoice_id", uuid, nullable=False),
        sa.Column("format_version", sa.String(30), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "invoice_id", "format_version", name="uq_billing_exports_invoice_version"
        ),
        sa.UniqueConstraint("idempotency_key", name="uq_billing_exports_idempotency"),
        sa.ForeignKeyConstraint(["invoice_id"], ["billing_invoices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", uuid),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", uuid), sa.column("permission_id", uuid)
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            [
                {"id": stable_id("permission", code), "code": code, "description": desc}
                for code, desc in PERMISSIONS.items()
            ]
        )
        .on_conflict_do_nothing()
    )
    connection.execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role),
                    "permission_id": stable_id("permission", permission),
                }
                for role in ("administrator", "management", "accounting")
                for permission in PERMISSIONS
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM billing_exports)
                OR EXISTS (SELECT 1 FROM billing_payments)
                OR EXISTS (SELECT 1 FROM billing_invoice_lines)
                OR EXISTS (SELECT 1 FROM billing_invoices)
                OR EXISTS (SELECT 1 FROM billing_rates) THEN
                RAISE EXCEPTION
                    'Rechnungswesen-Downgrade abgelehnt: Finanzdaten zuerst sichern';
            END IF;
        END
        $$
        """
    )
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    role_permissions = sa.table(
        "role_permissions", sa.column("permission_id", postgresql.UUID(as_uuid=True))
    )
    permissions = sa.table("permissions", sa.column("id", postgresql.UUID(as_uuid=True)))
    connection = op.get_bind()
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_table("billing_exports")
    op.drop_index("ix_billing_payments_invoice_date", table_name="billing_payments")
    op.drop_table("billing_payments")
    op.drop_table("billing_invoice_lines")
    op.drop_index("ix_billing_invoices_status_due", table_name="billing_invoices")
    op.drop_index("ix_billing_invoices_customer_date", table_name="billing_invoices")
    op.drop_table("billing_invoices")
    op.drop_table("billing_rates")
