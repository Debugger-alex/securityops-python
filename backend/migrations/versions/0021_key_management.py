"""Add an object-scoped physical key register and append-only movements."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0021_key_management"
down_revision: str | None = "0020_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "keys.read": "Schlüsselregister und Schlüsselhistorien einsehen",
    "keys.manage": "Schlüsselstammdaten verwalten und archivieren",
    "keys.move": "Schlüssel ausgeben, zurücknehmen, melden und inventarisieren",
}
ROLE_PERMISSIONS = {
    "administrator": set(PERMISSIONS),
    "management": set(PERMISSIONS),
    "operations": set(PERMISSIONS),
    "object_manager": {"keys.read", "keys.move"},
}
ROLE_CODES = tuple(ROLE_PERMISSIONS)


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    timestamp = sa.DateTime(timezone=True)
    op.create_table(
        "physical_keys",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("key_number", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column(
            "object_id",
            uuid,
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column(
            "current_employee_id",
            uuid,
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("archived_at", timestamp, nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('available', 'issued', 'lost', 'defective', 'archived')",
            name="ck_physical_keys_status",
        ),
        sa.CheckConstraint("length(trim(key_number)) > 0", name="ck_physical_keys_number"),
        sa.CheckConstraint("length(trim(description)) > 0", name="ck_physical_keys_description"),
        sa.CheckConstraint(
            "(status = 'issued' AND current_employee_id IS NOT NULL) "
            "OR (status != 'issued' AND current_employee_id IS NULL)",
            name="ck_physical_keys_holder_status",
        ),
        sa.CheckConstraint(
            "(status = 'archived' AND archived_at IS NOT NULL) "
            "OR (status != 'archived' AND archived_at IS NULL)",
            name="ck_physical_keys_archived_at",
        ),
    )
    op.create_index(
        "ix_physical_keys_object_status",
        "physical_keys",
        ["object_id", "status", "archived_at"],
    )
    op.create_index(
        "ix_physical_keys_holder_status", "physical_keys", ["current_employee_id", "status"]
    )

    op.create_table(
        "key_movements",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "key_id",
            uuid,
            sa.ForeignKey("physical_keys.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "object_id", uuid, sa.ForeignKey("objects.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "employee_id",
            uuid,
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("actor_id", uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("key_status_after", sa.String(20), nullable=False),
        sa.Column("acknowledged_at", timestamp, nullable=True),
        sa.Column("acknowledgement_note", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", timestamp, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "movement_type IN ('issued', 'returned', 'lost', 'defective', 'inventory')",
            name="ck_key_movements_type",
        ),
        sa.CheckConstraint(
            "key_status_after IN ('available', 'issued', 'lost', 'defective')",
            name="ck_key_movements_status_after",
        ),
        sa.CheckConstraint(
            "movement_type != 'issued' OR "
            "(employee_id IS NOT NULL AND acknowledged_at IS NOT NULL)",
            name="ck_key_movements_issue_acknowledged",
        ),
        sa.CheckConstraint(
            "(movement_type = 'issued' AND key_status_after = 'issued') "
            "OR (movement_type = 'returned' AND key_status_after = 'available') "
            "OR (movement_type = 'lost' AND key_status_after = 'lost') "
            "OR (movement_type = 'defective' AND key_status_after = 'defective') "
            "OR (movement_type = 'inventory' AND key_status_after IN "
            "('available', 'issued'))",
            name="ck_key_movements_type_status",
        ),
    )
    op.create_index("ix_key_movements_key_created", "key_movements", ["key_id", "created_at"])
    op.create_index("ix_key_movements_object_created", "key_movements", ["object_id", "created_at"])
    op.create_index(
        "ix_key_movements_employee_created", "key_movements", ["employee_id", "created_at"]
    )

    op.execute(
        """
        CREATE FUNCTION securityops_reject_key_movement_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Schlüsselbewegungen sind unveränderlich'
                USING ERRCODE = '55000';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        "CREATE TRIGGER key_movements_append_only BEFORE UPDATE OR DELETE ON key_movements "
        "FOR EACH ROW EXECUTE FUNCTION securityops_reject_key_movement_mutation()"
    )

    uuid_type = postgresql.UUID(as_uuid=True)
    permissions = sa.table(
        "permissions",
        sa.column("id", uuid_type),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions", sa.column("role_id", uuid_type), sa.column("permission_id", uuid_type)
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            [
                {
                    "id": stable_id("permission", code),
                    "code": code,
                    "description": description,
                }
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
    has_data = connection.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM key_movements) OR EXISTS (SELECT 1 FROM physical_keys)"
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
                WHERE p.code IN ('keys.read', 'keys.manage', 'keys.move')
                  AND r.code NOT IN ('administrator', 'management', 'operations', 'object_manager')
            )
            """
        )
    ).scalar_one()
    if has_data or custom_role_permission:
        raise RuntimeError(
            "Schlüsselverwaltungs-Downgrade abgelehnt: Schlüssel, Bewegungsdaten oder "
            "benutzerdefinierte Berechtigungen zuerst sichern."
        )

    uuid = postgresql.UUID(as_uuid=True)
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    role_ids = [stable_id("role", code) for code in ROLE_CODES]
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
    op.execute("DROP TRIGGER key_movements_append_only ON key_movements")
    op.execute("DROP FUNCTION securityops_reject_key_movement_mutation()")
    op.drop_index("ix_key_movements_employee_created", table_name="key_movements")
    op.drop_index("ix_key_movements_object_created", table_name="key_movements")
    op.drop_index("ix_key_movements_key_created", table_name="key_movements")
    op.drop_table("key_movements")
    op.drop_index("ix_physical_keys_holder_status", table_name="physical_keys")
    op.drop_index("ix_physical_keys_object_status", table_name="physical_keys")
    op.drop_table("physical_keys")
