"""Add object-scoped incident and complaint management."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0022_incident_management"
down_revision: str | None = "0021_key_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "incidents.read": "Vorfälle im eigenen Objektbereich einsehen",
    "incidents.read_all": "Vorfälle objektübergreifend einsehen",
    "incidents.create": "Vorfälle und Beschwerden melden",
    "incidents.update": "Vorfälle im eigenen Objektbereich bearbeiten",
    "incidents.manage_all": "Vorfälle objektübergreifend verwalten",
    "incidents.sensitive.read": "Gesondert geschützte Vorfalldetails einsehen",
    "incidents.sensitive.manage": "Gesondert geschützte Vorfalldetails verwalten",
}
ROLE_PERMISSIONS = {
    "administrator": set(PERMISSIONS),
    "management": set(PERMISSIONS),
    "operations": {
        "incidents.read",
        "incidents.read_all",
        "incidents.create",
        "incidents.update",
        "incidents.sensitive.read",
        "incidents.sensitive.manage",
    },
    "object_manager": {
        "incidents.read",
        "incidents.create",
        "incidents.update",
        "incidents.sensitive.read",
    },
    "employee": {"incidents.read", "incidents.create"},
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "incidents",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("report", sa.Text(), nullable=False),
        sa.Column("incident_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("object_id", uuid, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="reported"),
        sa.Column("due_at", timestamp, nullable=True),
        sa.Column("assigned_to_id", uuid, nullable=False),
        sa.Column("owks_event_id", uuid, nullable=True),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "incident_type IN ('incident', 'accident', 'assault', 'property_damage', 'complaint', 'other')",
            name="ck_incidents_type",
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')", name="ck_incidents_severity"
        ),
        sa.CheckConstraint(
            "status IN ('reported', 'investigating', 'action_required', 'closed')",
            name="ck_incidents_status",
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_incidents_title"),
        sa.CheckConstraint("length(trim(report)) > 0", name="ck_incidents_report"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owks_event_id"], ["owks_events.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_incidents_object_status_due", "incidents", ["object_id", "status", "due_at"]
    )
    op.create_index("ix_incidents_assignee_status", "incidents", ["assigned_to_id", "status"])

    op.create_table(
        "incident_sensitive_details",
        sa.Column("incident_id", uuid, primary_key=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("closure_report", sa.Text(), nullable=True),
        sa.Column("updated_by_id", uuid, nullable=True),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "incident_measures",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("incident_id", uuid, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", timestamp, nullable=True),
        sa.Column("assigned_to_id", uuid, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'completed')", name="ck_incident_measures_status"
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_incident_measures_title"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_incident_measures_incident_status_due",
        "incident_measures",
        ["incident_id", "status", "due_at"],
    )
    op.create_index(
        "ix_incident_measures_assignee_status",
        "incident_measures",
        ["assigned_to_id", "status"],
    )

    op.create_table(
        "incident_people",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("incident_id", uuid, nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('involved', 'witness')", name="ck_incident_people_role"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_incident_people_name"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_incident_people_incident_created", "incident_people", ["incident_id", "created_at"]
    )

    op.create_table(
        "incident_attachments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("incident_id", uuid, nullable=False),
        sa.Column("storage_key", sa.String(32), nullable=False, unique=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by_id", uuid, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "media_type IN ('application/pdf', 'image/png', 'image/jpeg')",
            name="ck_incident_attachments_media_type",
        ),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760", name="ck_incident_attachments_size"
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_incident_attachments_incident_created",
        "incident_attachments",
        ["incident_id", "created_at"],
    )

    op.create_table(
        "incident_history",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("incident_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_incident_history_incident_created", "incident_history", ["incident_id", "created_at"]
    )

    op.execute(
        """
        CREATE FUNCTION securityops_reject_incident_history_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Vorfalldatenverlauf und Bezüge sind unveränderlich'
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    for table in ("incident_history", "incident_people", "incident_attachments"):
        op.execute(
            f"CREATE TRIGGER {table}_append_only BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION securityops_reject_incident_history_mutation()"
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
                {"id": stable_id("permission", code), "code": code, "description": description}
                for code, description in PERMISSIONS.items()
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
                for role_code, permission_codes in ROLE_PERMISSIONS.items()
                for permission_code in sorted(permission_codes)
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    connection = op.get_bind()
    uuid = postgresql.UUID(as_uuid=True)
    has_data = connection.execute(
        sa.text(
            """
            SELECT EXISTS (SELECT 1 FROM incidents)
                OR EXISTS (SELECT 1 FROM incident_sensitive_details)
                OR EXISTS (SELECT 1 FROM incident_measures)
                OR EXISTS (SELECT 1 FROM incident_people)
                OR EXISTS (SELECT 1 FROM incident_attachments)
                OR EXISTS (SELECT 1 FROM incident_history)
            """
        )
    ).scalar_one()
    custom_role_permission = connection.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.code IN (
                    'incidents.read', 'incidents.read_all', 'incidents.create',
                    'incidents.update', 'incidents.manage_all',
                    'incidents.sensitive.read', 'incidents.sensitive.manage'
                )
                  AND r.code NOT IN (
                    'administrator', 'management', 'operations', 'object_manager', 'employee'
                  )
            )
            """
        )
    ).scalar_one()
    if has_data or custom_role_permission:
        raise RuntimeError(
            "Vorfallmanagement-Downgrade abgelehnt: Vorfälle, Verlauf, Datei-/Personenbezüge "
            "oder benutzerdefinierte Berechtigungen zuerst sichern."
        )

    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    role_ids = [stable_id("role", code) for code in ROLE_PERMISSIONS]
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", uuid), sa.column("permission_id", uuid)
    )
    permissions = sa.table("permissions", sa.column("id", uuid))
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.permission_id.in_(permission_ids),
            role_permissions.c.role_id.in_(role_ids),
        )
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    for table in ("incident_history", "incident_people", "incident_attachments"):
        op.execute(f"DROP TRIGGER {table}_append_only ON {table}")
    op.execute("DROP FUNCTION securityops_reject_incident_history_mutation()")
    op.drop_index("ix_incident_history_incident_created", table_name="incident_history")
    op.drop_table("incident_history")
    op.drop_index("ix_incident_attachments_incident_created", table_name="incident_attachments")
    op.drop_table("incident_attachments")
    op.drop_index("ix_incident_people_incident_created", table_name="incident_people")
    op.drop_table("incident_people")
    op.drop_index("ix_incident_measures_assignee_status", table_name="incident_measures")
    op.drop_index("ix_incident_measures_incident_status_due", table_name="incident_measures")
    op.drop_table("incident_measures")
    op.drop_table("incident_sensitive_details")
    op.drop_index("ix_incidents_assignee_status", table_name="incidents")
    op.drop_index("ix_incidents_object_status_due", table_name="incidents")
    op.drop_table("incidents")
