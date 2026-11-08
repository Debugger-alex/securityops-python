"""Add users, RBAC, sessions, and audit log."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_identity_audit"
down_revision: str | None = "0001_customers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLE_ROWS = [
    ("administrator", "Administrator", "Vollzugriff auf alle Systembereiche."),
    ("management", "Geschäftsführung", "Unternehmensweite Einsicht und Verwaltung."),
    ("operations", "Einsatzleitung", "Operative Einsatz- und Objektverwaltung."),
    ("object_manager", "Objektleitung", "Verwaltung zugewiesener Objekte und Wachbuch."),
    ("hr", "Personalverwaltung", "Personal- und Qualifikationsverwaltung."),
    ("employee", "Mitarbeiter", "Zugriff auf eigene Einsätze und operative Erfassung."),
]

PERMISSION_ROWS = [
    ("dashboard.read", "Dashboard-Kennzahlen anzeigen"),
    ("customers.read", "Kunden anzeigen"),
    ("customers.create", "Kunden anlegen"),
    ("customers.update", "Kunden bearbeiten"),
    ("customers.archive", "Kunden archivieren"),
    ("objects.read", "Objekte anzeigen"),
    ("objects.manage", "Objekte verwalten"),
    ("employees.read", "Mitarbeiter anzeigen"),
    ("employees.manage", "Personal verwalten"),
    ("scheduling.read", "Dienstpläne anzeigen"),
    ("scheduling.manage", "Dienstpläne verwalten"),
    ("time.read", "Arbeitszeiten anzeigen"),
    ("time.manage", "Arbeitszeiten verwalten"),
    ("owks.read", "Wachbuch und Kontrollen anzeigen"),
    ("owks.create", "Wachbucheinträge und Kontrollen erfassen"),
    ("documents.read", "Dokumente anzeigen"),
    ("documents.manage", "Dokumente verwalten"),
    ("billing.read", "Abrechnungen anzeigen"),
    ("billing.manage", "Abrechnungen verwalten"),
    ("reports.read", "Auswertungen anzeigen"),
    ("users.read", "Benutzer anzeigen"),
    ("users.manage", "Benutzer verwalten"),
    ("roles.read", "Rollen und Rechte anzeigen"),
    ("audit.read", "Audit-Protokoll einsehen"),
]

ROLE_PERMISSIONS = {
    "administrator": {code for code, _ in PERMISSION_ROWS},
    "management": {
        "dashboard.read",
        "customers.read",
        "customers.create",
        "customers.update",
        "customers.archive",
        "objects.read",
        "objects.manage",
        "employees.read",
        "employees.manage",
        "scheduling.read",
        "scheduling.manage",
        "time.read",
        "time.manage",
        "owks.read",
        "documents.read",
        "documents.manage",
        "billing.read",
        "billing.manage",
        "reports.read",
        "users.read",
        "users.manage",
        "roles.read",
        "audit.read",
    },
    "operations": {
        "dashboard.read",
        "customers.read",
        "objects.read",
        "objects.manage",
        "employees.read",
        "scheduling.read",
        "scheduling.manage",
        "time.read",
        "owks.read",
        "owks.create",
        "documents.read",
        "reports.read",
    },
    "object_manager": {
        "dashboard.read",
        "objects.read",
        "scheduling.read",
        "owks.read",
        "owks.create",
        "documents.read",
    },
    "hr": {
        "dashboard.read",
        "employees.read",
        "employees.manage",
        "scheduling.read",
        "time.read",
        "documents.read",
    },
    "employee": {
        "scheduling.read",
        "time.read",
        "owks.read",
        "owks.create",
        "documents.read",
    },
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(300), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("length(trim(username)) > 0", name="ck_users_username"),
        sa.CheckConstraint("length(trim(full_name)) > 0", name="ck_users_full_name"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_sessions_user_expires", "user_sessions", ["user_id", "expires_at"])
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_audit_logs_entity_created", "audit_logs", ["entity_type", "entity_id", "created_at"]
    )
    op.create_index("ix_audit_logs_actor_created", "audit_logs", ["actor_id", "created_at"])

    roles = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
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
        roles,
        [
            {"id": stable_id("role", code), "code": code, "name": name, "description": description}
            for code, name, description in ROLE_ROWS
        ],
    )
    op.bulk_insert(
        permissions,
        [
            {"id": stable_id("permission", code), "code": code, "description": description}
            for code, description in PERMISSION_ROWS
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
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_user_sessions_user_expires", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.drop_table("permissions")
    op.drop_table("roles")
