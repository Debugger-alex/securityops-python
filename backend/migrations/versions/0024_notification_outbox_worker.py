"""Add persistent notification outbox worker state and attempt history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_notification_outbox_worker"
down_revision: str | None = "0023_control_room_permission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_notification_outbox_status", "notification_outbox", type_="check")
    op.create_check_constraint(
        "ck_notification_outbox_status",
        "notification_outbox",
        "status IN ('pending', 'processing', 'completed', 'failed', 'dead_letter')",
    )
    op.add_column(
        "notification_outbox",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_outbox",
        sa.Column("lock_token", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_notification_outbox_status_locked",
        "notification_outbox",
        ["status", "locked_at"],
    )
    op.create_table(
        "notification_outbox_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("outbox_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("event", sa.String(length=30), nullable=False),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "event IN ('claimed', 'succeeded', 'retry_scheduled', 'dead_lettered')",
            name="ck_notification_outbox_attempt_event",
        ),
        sa.CheckConstraint("attempt_number > 0", name="ck_notification_outbox_attempt_number"),
        sa.ForeignKeyConstraint(["outbox_id"], ["notification_outbox.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "outbox_id",
            "attempt_number",
            "event",
            name="uq_notification_outbox_attempt_event",
        ),
    )
    op.create_index(
        "ix_notification_outbox_attempts_outbox_created",
        "notification_outbox_attempts",
        ["outbox_id", "created_at"],
    )
    op.execute(
        """
        CREATE FUNCTION securityops_reject_notification_outbox_attempt_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Notification-Outbox-Versuche sind unveränderlich'
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER notification_outbox_attempts_append_only "
        "BEFORE UPDATE OR DELETE ON notification_outbox_attempts "
        "FOR EACH ROW EXECUTE FUNCTION "
        "securityops_reject_notification_outbox_attempt_mutation()"
    )


def downgrade() -> None:
    connection = op.get_bind()
    if connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM notification_outbox_attempts)")
    ).scalar_one():
        raise RuntimeError(
            "Notification-Worker-Downgrade abgelehnt: Attempt-Historie zuerst sichern."
        )
    op.execute(
        "DROP TRIGGER notification_outbox_attempts_append_only ON notification_outbox_attempts"
    )
    op.execute("DROP FUNCTION securityops_reject_notification_outbox_attempt_mutation()")
    op.drop_index(
        "ix_notification_outbox_attempts_outbox_created",
        table_name="notification_outbox_attempts",
    )
    op.drop_table("notification_outbox_attempts")
    op.drop_index("ix_notification_outbox_status_locked", table_name="notification_outbox")
    op.drop_column("notification_outbox", "lock_token")
    op.drop_column("notification_outbox", "locked_at")
    op.drop_constraint("ck_notification_outbox_status", "notification_outbox", type_="check")
    op.create_check_constraint(
        "ck_notification_outbox_status",
        "notification_outbox",
        "status IN ('pending', 'processing', 'completed', 'failed')",
    )
