"""Add scheduling core, timezone settings, and overlap protection."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_scheduling_core"
down_revision: str | None = "0010_customer_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedule_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("time_zone", sa.String(length=80), nullable=False),
        sa.Column("minimum_rest_hours", sa.Integer(), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "id = 1",
            name="ck_schedule_settings_singleton",
        ),
        sa.CheckConstraint(
            "minimum_rest_hours >= 0 AND minimum_rest_hours <= 168",
            name="ck_schedule_settings_rest_hours",
        ),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.execute(
        "INSERT INTO schedule_settings (id, time_zone, minimum_rest_hours) "
        "VALUES (1, 'Europe/Berlin', 11)"
    )
    op.create_table(
        "schedule_shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_qualification", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("ends_at > starts_at", name="ck_schedule_shifts_time_order"),
        sa.CheckConstraint("break_minutes >= 0", name="ck_schedule_shifts_break_minutes"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name="ck_schedule_shifts_status",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_schedule_shifts_employee_time",
        "schedule_shifts",
        ["employee_id", "starts_at", "ends_at"],
    )
    op.create_index(
        "ix_schedule_shifts_object_time",
        "schedule_shifts",
        ["object_id", "starts_at", "ends_at"],
    )
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        ALTER TABLE schedule_shifts
        ADD CONSTRAINT ex_schedule_shifts_employee_time
        EXCLUDE USING gist (
            employee_id WITH =,
            tstzrange(starts_at, ends_at, '[)') WITH &&
        )
        WHERE (status <> 'cancelled')
        """
    )
    op.create_table(
        "schedule_shift_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["shift_id"], ["schedule_shifts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_schedule_shift_history_shift_created",
        "schedule_shift_history",
        ["shift_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_shift_history_shift_created", table_name="schedule_shift_history")
    op.drop_table("schedule_shift_history")
    op.execute("ALTER TABLE schedule_shifts DROP CONSTRAINT ex_schedule_shifts_employee_time")
    op.drop_index("ix_schedule_shifts_object_time", table_name="schedule_shifts")
    op.drop_index("ix_schedule_shifts_employee_time", table_name="schedule_shifts")
    op.drop_table("schedule_shifts")
    op.drop_table("schedule_settings")
