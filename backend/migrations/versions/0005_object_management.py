"""Add customer objects, scoped access, and encrypted sensitive details."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_object_management"
down_revision: str | None = "0004_customer_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    ("objects.create", "Objekte anlegen"),
    ("objects.read_all", "Alle Objekte unabhängig von einer Zuweisung anzeigen"),
    ("objects.manage_all", "Alle Objekte unabhängig von einer Zuweisung verwalten"),
    ("objects.archive", "Objekte archivieren"),
    ("objects.assign", "Benutzer Objekten zuweisen"),
    ("objects.sensitive.read", "Sensible Objektangaben lesen"),
    ("objects.sensitive.write", "Sensible Objektangaben ändern"),
]

ROLE_GRANTS = {
    "administrator": {
        "objects.create",
        "objects.read_all",
        "objects.manage_all",
        "objects.archive",
        "objects.assign",
        "objects.sensitive.read",
        "objects.sensitive.write",
    },
    "management": {
        "objects.create",
        "objects.read_all",
        "objects.manage_all",
        "objects.archive",
        "objects.assign",
    },
    "operations": {"objects.create", "objects.read_all", "objects.assign"},
    "object_manager": set(),
    "auditor": {"objects.read_all"},
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("object_number", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("service_instructions", sa.Text(), nullable=True),
        sa.Column("street", sa.String(160), nullable=False),
        sa.Column("house_number", sa.String(30), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="DE"),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("operating_hours", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("required_staffing", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "qualification_requirements",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "object_manager_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("status IN ('active', 'inactive')", name="ck_objects_status"),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_objects_name"),
        sa.CheckConstraint("required_staffing >= 0", name="ck_objects_required_staffing"),
    )
    op.create_index("ix_objects_customer_status", "objects", ["customer_id", "status"])
    op.create_table(
        "object_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("responsibility", sa.String(120), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint(
            "length(trim(first_name)) > 0 AND length(trim(last_name)) > 0",
            name="ck_object_contacts_name",
        ),
    )
    op.create_index(
        "uq_object_contacts_primary",
        "object_contacts",
        ["object_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )
    op.create_table(
        "object_user_assignments",
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "assigned_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_object_user_assignments_user", "object_user_assignments", ["user_id"])
    op.create_table(
        "object_sensitive_data",
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_table(
        "object_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_object_history_object_created", "object_history", ["object_id", "created_at"]
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
            {"id": stable_id("permission", code), "code": code, "description": description}
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
            for role_code, permission_codes in ROLE_GRANTS.items()
            for permission_code in sorted(permission_codes)
        ],
    )
    connection = op.get_bind()
    connection.execute(
        role_permissions.insert().values(
            role_id=stable_id("role", "object_manager"),
            permission_id=stable_id("permission", "objects.manage"),
        )
    )


def downgrade() -> None:
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    connection = op.get_bind()
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.role_id == stable_id("role", "object_manager"),
            role_permissions.c.permission_id == stable_id("permission", "objects.manage"),
        )
    )
    permission_ids = [stable_id("permission", code) for code, _ in PERMISSIONS]
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_object_history_object_created", table_name="object_history")
    op.drop_table("object_history")
    op.drop_table("object_sensitive_data")
    op.drop_index("ix_object_user_assignments_user", table_name="object_user_assignments")
    op.drop_table("object_user_assignments")
    op.drop_index("uq_object_contacts_primary", table_name="object_contacts")
    op.drop_table("object_contacts")
    op.drop_index("ix_objects_customer_status", table_name="objects")
    op.drop_table("objects")
