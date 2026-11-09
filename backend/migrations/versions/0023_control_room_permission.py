"""Add permission for the object-scoped control room."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0023_control_room_permission"
down_revision: str | None = "0022_incident_management"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION_CODE = "control_room.read"
ROLE_CODES = ("administrator", "management", "operations", "object_manager")


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    permissions = sa.table(
        "permissions",
        sa.column("id", uuid),
        sa.column("code", sa.String),
        sa.column("description", sa.String),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", uuid),
        sa.column("permission_id", uuid),
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            id=stable_id("permission", PERMISSION_CODE),
            code=PERMISSION_CODE,
            description="Berechtigungsgefilterte Leitstellenübersicht einsehen",
        )
        .on_conflict_do_nothing()
    )
    connection.execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role_code),
                    "permission_id": stable_id("permission", PERMISSION_CODE),
                }
                for role_code in ROLE_CODES
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    connection = op.get_bind()
    permission_id = stable_id("permission", PERMISSION_CODE)
    custom_role_permission = connection.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.code = :permission_code
                  AND r.code NOT IN (
                    'administrator', 'management', 'operations', 'object_manager'
                  )
            )
            """
        ),
        {"permission_code": PERMISSION_CODE},
    ).scalar_one()
    if custom_role_permission:
        raise RuntimeError(
            "Leitstellen-Downgrade abgelehnt: Die Berechtigung ist benutzerdefinierten Rollen "
            "zugewiesen."
        )
    uuid = postgresql.UUID(as_uuid=True)
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", uuid),
        sa.column("permission_id", uuid),
    )
    permissions = sa.table("permissions", sa.column("id", uuid))
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.permission_id == permission_id,
            role_permissions.c.role_id.in_([stable_id("role", code) for code in ROLE_CODES]),
        )
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id == permission_id))
