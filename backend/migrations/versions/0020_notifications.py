"""Add task notification records and a durable notification outbox."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0020_notifications"
down_revision: str | None = "0019_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION = {
    "notifications.read_own": "Eigene In-App-Benachrichtigungen einsehen und als gelesen markieren"
}
ROLE_CODES = ("administrator", "management", "operations", "employee")


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "notification_outbox",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("dedupe_key", sa.String(160), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("aggregate_type", sa.String(80), nullable=False),
        sa.Column("aggregate_id", uuid, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("last_attempt_at", timestamp, nullable=True),
        sa.Column("processed_at", timestamp, nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_notification_outbox_status",
        ),
        sa.CheckConstraint("attempt_count >= 0", name="ck_notification_outbox_attempt_count"),
        sa.UniqueConstraint("dedupe_key", name="uq_notification_outbox_dedupe_key"),
    )
    op.create_index(
        "ix_notification_outbox_status_available",
        "notification_outbox",
        ["status", "available_at"],
    )
    op.create_table(
        "notifications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("outbox_id", uuid, nullable=False),
        sa.Column("recipient_id", uuid, nullable=False),
        sa.Column("task_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.String(500), nullable=False),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", timestamp, nullable=True),
        sa.ForeignKeyConstraint(["outbox_id"], ["notification_outbox.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("outbox_id", "recipient_id", name="uq_notifications_event_recipient"),
    )
    op.create_index(
        "ix_notifications_recipient_created", "notifications", ["recipient_id", "created_at"]
    )

    uuid_type = postgresql.UUID(as_uuid=True)
    permissions = sa.table(
        "permissions",
        sa.column("id", uuid_type),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", uuid_type), sa.column("permission_id", uuid_type)
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            [
                {
                    "id": stable_id("permission", code),
                    "code": code,
                    "description": description,
                }
                for code, description in PERMISSION.items()
            ]
        )
        .on_conflict_do_nothing()
    )
    connection.execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role_code),
                    "permission_id": stable_id("permission", permission_code),
                }
                for role_code in ROLE_CODES
                for permission_code in PERMISSION
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    connection = op.get_bind()
    uuid = postgresql.UUID(as_uuid=True)
    custom_role_permission = connection.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.code = 'notifications.read_own'
                  AND r.code NOT IN ('administrator', 'management', 'operations', 'employee')
            )
            """
        )
    ).scalar_one()
    has_records = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM notifications) "
            "OR EXISTS (SELECT 1 FROM notification_outbox)"
        )
    ).scalar_one()
    if custom_role_permission or has_records:
        raise RuntimeError(
            "Benachrichtigungs-Downgrade abgelehnt: Vorhandene Benachrichtigungen, "
            "Outbox-Ereignisse oder benutzerdefinierte Berechtigungen zuerst sichern."
        )

    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", uuid),
        sa.column("permission_id", uuid),
    )
    permissions = sa.table("permissions", sa.column("id", uuid))
    permission_ids = [stable_id("permission", code) for code in PERMISSION]
    role_ids = [stable_id("role", code) for code in ROLE_CODES]
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.permission_id.in_(permission_ids),
            role_permissions.c.role_id.in_(role_ids),
        )
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_notification_outbox_status_available", table_name="notification_outbox")
    op.drop_table("notification_outbox")
