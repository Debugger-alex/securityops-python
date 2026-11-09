"""Add the generic task core."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0019_tasks"
down_revision: str | None = "0018_identity_security"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "tasks.read_own": "Eigene und Objekte im eigenen Zuständigkeitsbereich einsehen",
    "tasks.read_all": "Alle Aufgaben einsehen",
    "tasks.create": "Aufgaben erstellen",
    "tasks.update_own": "Eigene und Aufgaben im eigenen Zuständigkeitsbereich bearbeiten",
    "tasks.manage": "Aufgaben im freigegebenen Bereich bearbeiten",
    "tasks.assign": "Aufgaben anderen aktiven Benutzern zuweisen",
    "tasks.manage_all": "Alle Aufgaben unabhängig vom Zuständigkeitsbereich verwalten",
}

ROLE_PERMISSIONS = {
    "administrator": set(PERMISSIONS),
    "management": {
        "tasks.read_all",
        "tasks.create",
        "tasks.manage",
        "tasks.assign",
    },
    "operations": {"tasks.read_own", "tasks.create", "tasks.update_own"},
    "employee": {"tasks.read_own", "tasks.create", "tasks.update_own"},
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "tasks",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assigned_to_id", uuid, nullable=False),
        sa.Column("created_by_id", uuid, nullable=True),
        sa.Column("customer_id", uuid, nullable=True),
        sa.Column("object_id", uuid, nullable=True),
        sa.Column("due_at", timestamp, nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("completion_evidence", sa.Text(), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')", name="ck_tasks_priority"
        ),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'blocked', 'completed', 'cancelled')",
            name="ck_tasks_status",
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_tasks_title"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_tasks_assignee_status_due", "tasks", ["assigned_to_id", "status", "due_at"])
    op.create_index("ix_tasks_object_status_due", "tasks", ["object_id", "status", "due_at"])
    op.create_index("ix_tasks_customer_status_due", "tasks", ["customer_id", "status", "due_at"])

    op.create_table(
        "task_comments",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("task_id", uuid, nullable=False),
        sa.Column("author_id", uuid, nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint("length(trim(body)) > 0", name="ck_task_comments_body"),
    )
    op.create_index("ix_task_comments_task_created", "task_comments", ["task_id", "created_at"])

    op.create_table(
        "task_history",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("task_id", uuid, nullable=False),
        sa.Column("actor_id", uuid, nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_task_history_task_created", "task_history", ["task_id", "created_at"])

    permissions = sa.table(
        "permissions",
        sa.column("id", uuid),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", uuid), sa.column("permission_id", uuid)
    )
    op.get_bind().execute(
        pg_insert(permissions)
        .values(
            [
                {"id": stable_id("permission", code), "code": code, "description": description}
                for code, description in PERMISSIONS.items()
            ]
        )
        .on_conflict_do_nothing()
    )
    op.get_bind().execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role_code),
                    "permission_id": stable_id("permission", permission_code),
                }
                for role_code, codes in ROLE_PERMISSIONS.items()
                for permission_code in codes
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    connection = op.get_bind()
    existing_tasks = connection.execute(sa.text("SELECT EXISTS (SELECT 1 FROM tasks)")).scalar_one()
    uuid = postgresql.UUID(as_uuid=True)
    role_ids = [stable_id("role", code) for code in ROLE_PERMISSIONS]
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", uuid),
        sa.column("permission_id", uuid),
    )
    roles_table = sa.table(
        "roles",
        sa.column("id", uuid),
        sa.column("code", sa.String(50)),
    )
    permissions_table = sa.table(
        "permissions",
        sa.column("id", uuid),
        sa.column("code", sa.String(100)),
    )
    custom_role_permission = connection.execute(
        sa.select(sa.literal(True))
        .select_from(
            role_permissions_table.join(
                roles_table, role_permissions_table.c.role_id == roles_table.c.id
            ).join(
                permissions_table,
                role_permissions_table.c.permission_id == permissions_table.c.id,
            )
        )
        .where(
            permissions_table.c.id.in_(permission_ids),
            roles_table.c.id.not_in(role_ids),
        )
        .limit(1)
    ).first()
    if existing_tasks or custom_role_permission is not None:
        raise RuntimeError(
            "Aufgaben-Downgrade abgelehnt: Vorhandene Aufgaben oder benutzerdefinierte "
            "Aufgabenberechtigungen zuerst sichern."
        )

    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", uuid),
        sa.column("permission_id", uuid),
    )
    permissions = sa.table("permissions", sa.column("id", uuid))
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.permission_id.in_(permission_ids),
            role_permissions.c.role_id.in_(role_ids),
        )
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))

    op.drop_index("ix_task_history_task_created", table_name="task_history")
    op.drop_table("task_history")
    op.drop_index("ix_task_comments_task_created", table_name="task_comments")
    op.drop_table("task_comments")
    op.drop_index("ix_tasks_customer_status_due", table_name="tasks")
    op.drop_index("ix_tasks_object_status_due", table_name="tasks")
    op.drop_index("ix_tasks_assignee_status_due", table_name="tasks")
    op.drop_table("tasks")
