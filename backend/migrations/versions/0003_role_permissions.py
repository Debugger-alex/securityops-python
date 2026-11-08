"""Expand standard roles and guard administrator assignment."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_role_permissions"
down_revision: str | None = "0002_identity_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_ROLES = [
    ("administration", "Verwaltung", "Kunden- und Dokumentenverwaltung ohne Systemadministration."),
    ("accounting", "Buchhaltung", "Zugriff auf Abrechnung und kaufmännische Auswertungen."),
    ("auditor", "Auditor", "Schreibgeschützter Einblick und Zugriff auf Audit-Protokolle."),
]

NEW_PERMISSIONS = [
    ("customers.delete", "Kunden löschen (nur für explizit freigegebene Abläufe)"),
    ("schedules.manage", "Dienstpläne verwalten"),
    ("time_tracking.approve", "Arbeitszeitkorrekturen freigeben"),
    ("invoices.manage", "Rechnungen verwalten"),
    ("owks.manage", "Wachbuch und Kontrollpunkte verwalten"),
    ("users.manage_admin", "Administratorrechte vergeben oder ändern"),
]


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    permissions_table = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions_table = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )

    op.bulk_insert(
        roles_table,
        [
            {"id": stable_id("role", code), "code": code, "name": name, "description": description}
            for code, name, description in NEW_ROLES
        ],
    )
    op.bulk_insert(
        permissions_table,
        [
            {"id": stable_id("permission", code), "code": code, "description": description}
            for code, description in NEW_PERMISSIONS
        ],
    )

    administrator_id = stable_id("role", "administrator")
    matrix = {
        "administrator": {
            "customers.delete",
            "schedules.manage",
            "time_tracking.approve",
            "invoices.manage",
            "owks.manage",
            "users.manage_admin",
        },
        "management": {
            "customers.delete",
            "schedules.manage",
            "time_tracking.approve",
            "invoices.manage",
            "owks.manage",
        },
        "operations": {"schedules.manage", "owks.manage"},
        "hr": {"time_tracking.approve"},
        "administration": {
            "dashboard.read",
            "customers.read",
            "customers.create",
            "customers.update",
            "objects.read",
            "documents.read",
            "documents.manage",
        },
        "accounting": {
            "dashboard.read",
            "customers.read",
            "billing.read",
            "billing.manage",
            "invoices.manage",
            "reports.read",
        },
        "auditor": {
            "dashboard.read",
            "customers.read",
            "objects.read",
            "employees.read",
            "scheduling.read",
            "time.read",
            "owks.read",
            "documents.read",
            "billing.read",
            "reports.read",
            "audit.read",
        },
    }
    all_permission_codes = {code for code, _ in NEW_PERMISSIONS} | {
        "dashboard.read",
        "customers.read",
        "customers.create",
        "customers.update",
        "objects.read",
        "employees.read",
        "scheduling.read",
        "time.read",
        "owks.read",
        "documents.read",
        "documents.manage",
        "billing.read",
        "billing.manage",
        "reports.read",
        "audit.read",
    }
    permission_ids = {code: stable_id("permission", code) for code in all_permission_codes}
    rows = [
        {
            "role_id": (
                administrator_id if role_code == "administrator" else stable_id("role", role_code)
            ),
            "permission_id": permission_ids[permission_code],
        }
        for role_code, permission_codes in matrix.items()
        for permission_code in sorted(permission_codes)
    ]
    op.bulk_insert(role_permissions_table, rows)


def downgrade() -> None:
    connection = op.get_bind()
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
    )
    roles = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
    )
    added_permission_ids = [stable_id("permission", code) for code, _ in NEW_PERMISSIONS]
    added_role_ids = [stable_id("role", code) for code, _, _ in NEW_ROLES]
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(added_permission_ids)))
    connection.execute(sa.delete(roles).where(roles.c.id.in_(added_role_ids)))
