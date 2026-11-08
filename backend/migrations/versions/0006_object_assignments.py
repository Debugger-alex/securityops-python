"""Add object assignments and scoped object permissions."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_object_assignments"
down_revision: str | None = "0005_object_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    ("objects.read_all", "Alle Objekte unabhängig von einer Zuweisung anzeigen"),
    ("objects.manage_all", "Alle Objekte unabhängig von einer Zuweisung verwalten"),
    ("objects.assign", "Benutzer Objekten zuweisen"),
]

ROLE_PERMISSIONS = {
    "administrator": {"objects.read_all", "objects.manage_all", "objects.assign"},
    "management": {"objects.read_all", "objects.manage_all", "objects.assign"},
    "operations": {"objects.read_all", "objects.manage_all", "objects.assign"},
    "object_manager": {"objects.manage"},
    "employee": {"objects.read"},
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "object_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("object_id", "user_id", name="uq_object_assignments_object_user"),
    )
    op.create_index(
        "ix_object_assignments_user_object", "object_assignments", ["user_id", "object_id"]
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    op.bulk_insert(
        permissions,
        [
            {
                "id": stable_id("permission", code),
                "code": code,
                "description": description,
            }
            for code, description in PERMISSIONS
        ],
    )
    op.bulk_insert(
        role_permissions,
        [
            {
                "role_id": stable_id("role", role_code),
                "permission_id": stable_id("permission", permission_code),
            }
            for role_code, permission_codes in ROLE_PERMISSIONS.items()
            for permission_code in sorted(permission_codes)
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
    )
    permission_ids = [stable_id("permission", code) for code, _ in PERMISSIONS]
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_object_assignments_user_object", table_name="object_assignments")
    op.drop_table("object_assignments")
