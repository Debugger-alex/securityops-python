"""Add auditable time tracking entries, segments, corrections, and permissions."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_time_tracking"
down_revision: str | None = "0011_scheduling_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "time_tracking.read_own": "Eigene Arbeitszeiten einsehen",
    "time_tracking.read_all": "Zulässige Arbeitszeiten einsehen",
    "time_tracking.create": "Arbeitszeit erfassen",
    "time_tracking.correct_own": "Korrekturen eigener Arbeitszeiten beantragen",
    "time_tracking.correct_all": "Korrekturen zulässiger Arbeitszeiten beantragen",
    "time_tracking.approve": "Arbeitszeiten und Korrekturen freigeben",
    "time_tracking.reject": "Arbeitszeiten und Korrekturen ablehnen",
    "time_tracking.export": "Arbeitszeitdaten exportieren",
    "time_tracking.manage": "Manuelle Arbeitszeiten verwalten",
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "time_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('open', 'submitted', 'approved', 'rejected', "
            "'correction_requested', 'locked')",
            name="ck_time_entries_status",
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="ck_time_entries_time_order",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["shift_id"], ["schedule_shifts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("employee_id", "shift_id", name="uq_time_entries_employee_shift"),
    )
    op.create_index("ix_time_entries_employee_start", "time_entries", ["employee_id", "started_at"])
    op.create_index("ix_time_entries_object_start", "time_entries", ["object_id", "started_at"])
    op.create_index("ix_time_entries_status_start", "time_entries", ["status", "started_at"])
    op.create_index(
        "uq_time_entries_one_open_per_employee",
        "time_entries",
        ["employee_id"],
        unique=True,
        sqlite_where=sa.text("status = 'open'"),
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "time_entry_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("kind IN ('work', 'break')", name="ck_time_entry_segments_kind"),
        sa.CheckConstraint("position > 0", name="ck_time_entry_segments_position"),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at > started_at",
            name="ck_time_entry_segments_time_order",
        ),
        sa.ForeignKeyConstraint(["entry_id"], ["time_entries.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("entry_id", "position", name="uq_time_entry_segments_position"),
    )
    op.create_index("ix_time_entry_segments_entry", "time_entry_segments", ["entry_id", "position"])
    op.create_index(
        "uq_time_entry_segments_one_open",
        "time_entry_segments",
        ["entry_id"],
        unique=True,
        sqlite_where=sa.text("ended_at IS NULL"),
        postgresql_where=sa.text("ended_at IS NULL"),
    )

    op.create_table(
        "time_entry_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("previous_status", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("decided_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_time_entry_corrections_status",
        ),
        sa.CheckConstraint("length(trim(reason)) > 0", name="ck_time_entry_corrections_reason"),
        sa.ForeignKeyConstraint(["entry_id"], ["time_entries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_time_entry_corrections_entry_created",
        "time_entry_corrections",
        ["entry_id", "requested_at"],
    )
    op.create_index(
        "uq_time_entry_corrections_pending",
        "time_entry_corrections",
        ["entry_id"],
        unique=True,
        sqlite_where=sa.text("status = 'pending'"),
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_table(
        "time_entry_correction_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("correction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "kind IN ('work', 'break')", name="ck_time_entry_correction_segments_kind"
        ),
        sa.CheckConstraint("position > 0", name="ck_time_entry_correction_segments_position"),
        sa.CheckConstraint(
            "ended_at > started_at", name="ck_time_entry_correction_segments_time_order"
        ),
        sa.ForeignKeyConstraint(
            ["correction_id"], ["time_entry_corrections.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint(
            "correction_id", "position", name="uq_time_entry_correction_segments_pos"
        ),
    )
    op.create_table(
        "time_entry_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("details", sa.JSON(), server_default="{}", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["entry_id"], ["time_entries.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_time_entry_history_entry_created", "time_entry_history", ["entry_id", "created_at"]
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
    permissions_by_role = {
        "administrator": set(PERMISSIONS),
        "management": {
            "time_tracking.read_all",
            "time_tracking.create",
            "time_tracking.correct_all",
            "time_tracking.approve",
            "time_tracking.reject",
            "time_tracking.export",
            "time_tracking.manage",
        },
        "hr": {
            "time_tracking.read_all",
            "time_tracking.create",
            "time_tracking.correct_all",
            "time_tracking.approve",
            "time_tracking.reject",
            "time_tracking.export",
            "time_tracking.manage",
        },
        "operations": {
            "time_tracking.read_all",
            "time_tracking.approve",
            "time_tracking.reject",
        },
        "object_manager": {
            "time_tracking.read_all",
            "time_tracking.approve",
            "time_tracking.reject",
        },
        "employee": {
            "time_tracking.read_own",
            "time_tracking.create",
            "time_tracking.correct_own",
        },
    }
    role_rows = []
    for role_code, codes in permissions_by_role.items():
        role_id = stable_id("role", role_code)
        role_rows.extend(
            {
                "role_id": role_id,
                "permission_id": stable_id("permission", permission_code),
            }
            for permission_code in sorted(codes)
        )
    op.bulk_insert(role_permissions, role_rows)


def downgrade() -> None:
    op.drop_index("ix_time_entry_history_entry_created", table_name="time_entry_history")
    op.drop_table("time_entry_history")
    op.drop_table("time_entry_correction_segments")
    op.drop_index("uq_time_entry_corrections_pending", table_name="time_entry_corrections")
    op.drop_index("ix_time_entry_corrections_entry_created", table_name="time_entry_corrections")
    op.drop_table("time_entry_corrections")
    op.drop_index("uq_time_entry_segments_one_open", table_name="time_entry_segments")
    op.drop_index("ix_time_entry_segments_entry", table_name="time_entry_segments")
    op.drop_table("time_entry_segments")
    op.drop_index("uq_time_entries_one_open_per_employee", table_name="time_entries")
    op.drop_index("ix_time_entries_status_start", table_name="time_entries")
    op.drop_index("ix_time_entries_object_start", table_name="time_entries")
    op.drop_index("ix_time_entries_employee_start", table_name="time_entries")
    op.drop_table("time_entries")

    connection = op.get_bind()
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code"),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
