"""Add employee availability, scheduling requests, and replacement audit details."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0016_scheduling_availability"
down_revision: str | None = "0015_documents_contracts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION = (
    "scheduling.availability.request",
    "Eigene Dienstwünsche und Sperrzeiten zur Prüfung einreichen",
)
REQUEST_ROLES = ("administrator", "management", "operations", "object_manager", "hr", "employee")


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "employee_availability_windows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("starts_at", sa.Time(), nullable=False),
        sa.Column("ends_at", sa.Time(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_employee_availability_weekday"),
        sa.CheckConstraint(
            "ends_at > starts_at",
            name="ck_employee_availability_window_time_order",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_employee_availability_windows_employee_weekday",
        "employee_availability_windows",
        ["employee_id", "weekday"],
    )

    op.create_table(
        "schedule_availability_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "kind IN ('preferred', 'blocked')",
            name="ck_schedule_availability_requests_kind",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'accepted', 'rejected')",
            name="ck_schedule_availability_requests_status",
        ),
        sa.CheckConstraint(
            "ends_at > starts_at",
            name="ck_schedule_availability_requests_time_order",
        ),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_schedule_availability_requests_employee_time",
        "schedule_availability_requests",
        ["employee_id", "starts_at", "ends_at"],
    )
    op.create_index(
        "ix_schedule_availability_requests_status_time",
        "schedule_availability_requests",
        ["status", "starts_at", "ends_at"],
    )
    op.add_column(
        "schedule_shift_history",
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            id=stable_id("permission", PERMISSION[0]),
            code=PERMISSION[0],
            description=PERMISSION[1],
        )
        .on_conflict_do_nothing()
    )
    connection.execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role_code),
                    "permission_id": stable_id("permission", PERMISSION[0]),
                }
                for role_code in REQUEST_ROLES
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM employee_availability_windows)
                OR EXISTS (SELECT 1 FROM schedule_availability_requests)
                OR EXISTS (
                    SELECT 1 FROM schedule_shift_history
                    WHERE details::jsonb <> '{}'::jsonb
                ) THEN
                RAISE EXCEPTION
                    'Dienstplan-Downgrade abgelehnt: Verfügbarkeits- oder Vertretungsdaten zuerst sichern';
            END IF;
        END
        $$
        """
    )

    permission_id = stable_id("permission", PERMISSION[0])
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    connection = op.get_bind()
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id == permission_id)
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id == permission_id))

    op.drop_column("schedule_shift_history", "details")
    op.drop_index(
        "ix_schedule_availability_requests_status_time",
        table_name="schedule_availability_requests",
    )
    op.drop_index(
        "ix_schedule_availability_requests_employee_time",
        table_name="schedule_availability_requests",
    )
    op.drop_table("schedule_availability_requests")
    op.drop_index(
        "ix_employee_availability_windows_employee_weekday",
        table_name="employee_availability_windows",
    )
    op.drop_table("employee_availability_windows")
