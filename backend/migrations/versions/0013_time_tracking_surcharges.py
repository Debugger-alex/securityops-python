"""Add configurable time surcharges and immutable payroll-period snapshots."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_time_tracking_surcharges"
down_revision: str | None = "0012_time_tracking"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "time_tracking.surcharges.read": "Zuschlagsregeln und Berechnungsnachweise einsehen",
    "time_tracking.surcharges.manage": "Zuschlagsregeln und Bundesland konfigurieren",
    "time_tracking.periods.read": "Gesperrte Abrechnungszeiträume einsehen",
    "time_tracking.periods.lock": "Abrechnungszeiträume nach Prüfung sperren",
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "time_tracking_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("federal_state", sa.String(length=2), nullable=True),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_time_tracking_settings_singleton"),
        sa.CheckConstraint(
            "federal_state IS NULL OR federal_state IN "
            "('BW', 'BY', 'BE', 'BB', 'HB', 'HH', 'HE', 'MV', 'NI', 'NW', 'RP', 'SL', 'SN', 'ST', 'SH', 'TH')",
            name="ck_time_tracking_settings_federal_state",
        ),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_table(
        "time_surcharge_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("calculation_type", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("basis_description", sa.String(length=240), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column(
            "combination_mode", sa.String(length=20), server_default="exclusive", nullable=False
        ),
        sa.Column("weekdays", sa.JSON(), nullable=False),
        sa.Column("starts_local", sa.String(length=5), nullable=True),
        sa.Column("ends_local", sa.String(length=5), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "category IN ('night', 'saturday', 'sunday', 'public_holiday', 'business')",
            name="ck_time_surcharge_rules_category",
        ),
        sa.CheckConstraint(
            "calculation_type IN ('percentage', 'fixed')",
            name="ck_time_surcharge_rules_calculation_type",
        ),
        sa.CheckConstraint("value > 0", name="ck_time_surcharge_rules_value"),
        sa.CheckConstraint(
            "valid_to IS NULL OR valid_to >= valid_from",
            name="ck_time_surcharge_rules_validity",
        ),
        sa.CheckConstraint(
            "combination_mode IN ('exclusive', 'combine')",
            name="ck_time_surcharge_rules_combination",
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_time_surcharge_rules_code"),
    )
    op.create_index(
        "ix_time_surcharge_rules_validity", "time_surcharge_rules", ["valid_from", "valid_to"]
    )
    op.create_table(
        "time_surcharge_calculations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("gross_work_seconds", sa.String(length=32), nullable=False),
        sa.Column("time_zone", sa.String(length=80), nullable=False),
        sa.Column("federal_state", sa.String(length=2), nullable=True),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("allocation_snapshot", sa.JSON(), nullable=False),
        sa.Column("source_segments", sa.JSON(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("version > 0", name="ck_time_surcharge_calculations_version"),
        sa.CheckConstraint(
            "length(gross_work_seconds) > 0",
            name="ck_time_surcharge_calculations_work_seconds",
        ),
        sa.ForeignKeyConstraint(["entry_id"], ["time_entries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("entry_id", "version", name="uq_time_surcharge_calculations_version"),
    )
    op.create_index(
        "ix_time_surcharge_calculations_entry_created",
        "time_surcharge_calculations",
        ["entry_id", "created_at"],
    )
    op.create_table(
        "time_tracking_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("time_zone", sa.String(length=80), nullable=False),
        sa.Column("federal_state", sa.String(length=2), nullable=True),
        sa.Column("locked_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("to_date >= from_date", name="ck_time_tracking_periods_date_order"),
        sa.ForeignKeyConstraint(["locked_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("from_date", "to_date", name="uq_time_tracking_periods_range"),
    )
    op.create_index(
        "ix_time_tracking_periods_range",
        "time_tracking_periods",
        ["from_date", "to_date"],
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(length=100)),
        sa.column("description", sa.String(length=300)),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    op.bulk_insert(
        permissions,
        [
            {"id": stable_id("permission", code), "code": code, "description": description}
            for code, description in PERMISSIONS.items()
        ],
    )
    role_rows = []
    roles = {
        "administrator": set(PERMISSIONS),
        "management": set(PERMISSIONS),
        "hr": set(PERMISSIONS),
    }
    for role_code, codes in roles.items():
        role_rows.extend(
            {
                "role_id": stable_id("role", role_code),
                "permission_id": stable_id("permission", permission_code),
            }
            for permission_code in sorted(codes)
        )
    op.bulk_insert(role_permissions, role_rows)


def downgrade() -> None:
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    connection = op.get_bind()
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_time_tracking_periods_range", table_name="time_tracking_periods")
    op.drop_table("time_tracking_periods")
    op.drop_index(
        "ix_time_surcharge_calculations_entry_created", table_name="time_surcharge_calculations"
    )
    op.drop_table("time_surcharge_calculations")
    op.drop_index("ix_time_surcharge_rules_validity", table_name="time_surcharge_rules")
    op.drop_table("time_surcharge_rules")
    op.drop_table("time_tracking_settings")
