"""Add object-bound digital logbook and patrol verification."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_owks_wachbuch"
down_revision: str | None = "0013_time_tracking_surcharges"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWKS_WRITE = "owks.write"


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "owks_control_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("identifier_type", sa.String(length=10), nullable=False),
        sa.Column("identifier_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("identifier_type IN ('qr', 'nfc')", name="ck_owks_control_point_type"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_owks_control_point_name"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("identifier_hash", name="uq_owks_control_points_identifier_hash"),
    )
    op.create_index(
        "ix_owks_control_points_object_active", "owks_control_points", ["object_id", "is_active"]
    )
    op.create_table(
        "owks_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_owks_route_name"),
        sa.CheckConstraint("interval_minutes > 0", name="ck_owks_route_interval"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_owks_routes_object_active", "owks_routes", ["object_id", "is_active"])
    op.create_table(
        "owks_route_points",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("control_point_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("position >= 0", name="ck_owks_route_points_position"),
        sa.ForeignKeyConstraint(["route_id"], ["owks_routes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["control_point_id"], ["owks_control_points.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("route_id", "position", name="uq_owks_route_points_position"),
        sa.UniqueConstraint("route_id", "control_point_id", name="uq_owks_route_points_point"),
    )
    op.create_table(
        "owks_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_owks_challenges_expires", "owks_challenges", ["expires_at"])
    op.create_table(
        "owks_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("route_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("control_point_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("corrects_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("client_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), server_default="info", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sync_status", sa.String(length=20), server_default="synced", nullable=False),
        sa.Column("presence_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "event_type IN ('entry', 'handover', 'control', 'manipulation', 'deviation', 'missed', 'notification', 'correction')",
            name="ck_owks_events_type",
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'critical')", name="ck_owks_events_severity"
        ),
        sa.CheckConstraint(
            "sync_status IN ('synced', 'conflict')", name="ck_owks_events_sync_status"
        ),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["route_id"], ["owks_routes.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["control_point_id"], ["owks_control_points.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["corrects_event_id"], ["owks_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["challenge_id"], ["owks_challenges.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("actor_id", "client_event_id", name="uq_owks_events_idempotency"),
    )
    op.create_index("ix_owks_events_object_occurred", "owks_events", ["object_id", "occurred_at"])
    op.create_index("ix_owks_events_object_created", "owks_events", ["object_id", "created_at"])
    op.create_index(
        "uq_owks_missed_event_client_id",
        "owks_events",
        ["client_event_id"],
        unique=True,
        postgresql_where=sa.text("event_type = 'missed'"),
    )
    op.create_table(
        "owks_event_statuses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.String(length=1000), server_default="", nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved')", name="ck_owks_event_status"
        ),
        sa.CheckConstraint("sequence_no > 0", name="ck_owks_event_status_sequence"),
        sa.ForeignKeyConstraint(["event_id"], ["owks_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("event_id", "sequence_no", name="uq_owks_event_status_sequence"),
    )
    op.create_index(
        "ix_owks_event_statuses_event_created",
        "owks_event_statuses",
        ["event_id", "created_at"],
    )
    op.create_table(
        "owks_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=200), nullable=False),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "media_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="ck_owks_attachments_media_type",
        ),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760", name="ck_owks_attachments_size"
        ),
        sa.ForeignKeyConstraint(["event_id"], ["owks_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_owks_attachments_event_created", "owks_attachments", ["event_id", "created_at"]
    )

    op.execute(
        """
        CREATE FUNCTION securityops_reject_owks_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'OWKS-Datensätze sind unveränderlich; Korrekturen müssen angehängt werden'
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in ("owks_events", "owks_event_statuses", "owks_attachments"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION securityops_reject_owks_mutation()"
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
    permission_id = stable_id("permission", OWKS_WRITE)
    op.bulk_insert(
        permissions,
        [
            {
                "id": permission_id,
                "code": OWKS_WRITE,
                "description": "Wachbuchereignisse erfassen und synchronisieren",
            }
        ],
    )
    op.bulk_insert(
        role_permissions,
        [
            {
                "role_id": stable_id("role", role_code),
                "permission_id": permission_id,
            }
            for role_code in (
                "administrator",
                "management",
                "operations",
                "object_manager",
                "employee",
            )
        ],
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM owks_control_points)
                OR EXISTS (SELECT 1 FROM owks_routes)
                OR EXISTS (SELECT 1 FROM owks_route_points)
                OR EXISTS (SELECT 1 FROM owks_challenges)
                OR EXISTS (SELECT 1 FROM owks_events)
                OR EXISTS (SELECT 1 FROM owks_event_statuses)
                OR EXISTS (SELECT 1 FROM owks_attachments) THEN
                RAISE EXCEPTION
                    'OWKS-Downgrade abgelehnt: Betriebsdaten zuerst sichern und separat archivieren';
            END IF;
        END
        $$
        """
    )
    connection = op.get_bind()
    permission_id = stable_id("permission", OWKS_WRITE)
    role_permissions = sa.table(
        "role_permissions",
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id == permission_id)
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id == permission_id))
    for table in ("owks_events", "owks_event_statuses", "owks_attachments"):
        op.execute(f"DROP TRIGGER {table}_append_only ON {table}")
    op.execute("DROP FUNCTION securityops_reject_owks_mutation()")
    op.drop_index("ix_owks_attachments_event_created", table_name="owks_attachments")
    op.drop_table("owks_attachments")
    op.drop_index("ix_owks_event_statuses_event_created", table_name="owks_event_statuses")
    op.drop_table("owks_event_statuses")
    op.drop_index("ix_owks_events_object_created", table_name="owks_events")
    op.drop_index("ix_owks_events_object_occurred", table_name="owks_events")
    op.drop_index("uq_owks_missed_event_client_id", table_name="owks_events")
    op.drop_table("owks_events")
    op.drop_index("ix_owks_challenges_expires", table_name="owks_challenges")
    op.drop_table("owks_challenges")
    op.drop_table("owks_route_points")
    op.drop_index("ix_owks_routes_object_active", table_name="owks_routes")
    op.drop_table("owks_routes")
    op.drop_index("ix_owks_control_points_object_active", table_name="owks_control_points")
    op.drop_table("owks_control_points")
