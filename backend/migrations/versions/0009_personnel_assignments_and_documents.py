"""Add employee object assignment history and qualification documents."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_personnel_links_docs"
down_revision: str | None = "0008_personnel_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    ("employees.documents.read", "Personaldokumente anzeigen"),
    ("employees.documents.manage", "Personaldokumente verwalten"),
]


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "employee_qualification_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "qualification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employee_qualifications.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(200), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column(
            "uploaded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "qualification_id", "version", name="uq_employee_qualification_documents_version"
        ),
        sa.CheckConstraint("version > 0", name="ck_employee_qualification_documents_version"),
        sa.CheckConstraint(
            "size_bytes > 0 AND size_bytes <= 10485760",
            name="ck_employee_qualification_documents_size",
        ),
        sa.CheckConstraint(
            "media_type IN ('application/pdf', 'image/jpeg', 'image/png')",
            name="ck_employee_qualification_documents_media_type",
        ),
        sa.CheckConstraint(
            "length(trim(file_name)) > 0", name="ck_employee_qualification_documents_name"
        ),
    )
    op.create_index(
        "ix_employee_qualification_documents_qualification_created",
        "employee_qualification_documents",
        ["qualification_id", "created_at"],
    )

    op.create_table(
        "employee_object_assignment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "action IN ('assigned', 'ended')", name="ck_employee_object_assignment_action"
        ),
    )
    op.create_index(
        "ix_employee_object_assignment_history_employee_created",
        "employee_object_assignment_history",
        ["employee_id", "created_at"],
    )
    op.create_index(
        "ix_employee_object_assignment_history_object_created",
        "employee_object_assignment_history",
        ["object_id", "created_at"],
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
            for role_code in ("administrator", "hr")
            for permission_code, _ in PERMISSIONS
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
    op.drop_index(
        "ix_employee_object_assignment_history_object_created",
        table_name="employee_object_assignment_history",
    )
    op.drop_index(
        "ix_employee_object_assignment_history_employee_created",
        table_name="employee_object_assignment_history",
    )
    op.drop_table("employee_object_assignment_history")
    op.drop_index(
        "ix_employee_qualification_documents_qualification_created",
        table_name="employee_qualification_documents",
    )
    op.drop_table("employee_qualification_documents")
