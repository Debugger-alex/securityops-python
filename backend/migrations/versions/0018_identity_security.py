"""Add MFA, session details, and guarded password resets."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0018_identity_security"
down_revision: str | None = "0017_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "sessions.manage": "Sitzungen anderer Benutzer einsehen und widerrufen",
    "users.password_reset": "Passwörter anderer Benutzer zurücksetzen",
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("mfa_last_counter", sa.BigInteger(), nullable=True))
    op.add_column(
        "users",
        sa.Column("force_password_change", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_check_constraint(
        "ck_users_mfa_secret", "users", "mfa_enabled = false OR mfa_secret_encrypted IS NOT NULL"
    )
    op.add_column("user_sessions", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("user_sessions", sa.Column("user_agent", sa.String(500), nullable=True))
    op.create_table(
        "user_mfa_recovery_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_user_mfa_recovery_codes_user_id", "user_mfa_recovery_codes", ["user_id"])

    uuid = postgresql.UUID(as_uuid=True)
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
                    "role_id": stable_id("role", "administrator"),
                    "permission_id": stable_id("permission", code),
                }
                for code in PERMISSIONS
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    connection = op.get_bind()
    protected_data_exists = connection.execute(
        sa.text(
            """
            SELECT EXISTS (
                SELECT 1 FROM users
                WHERE mfa_enabled OR mfa_secret_encrypted IS NOT NULL OR force_password_change
            ) OR EXISTS (SELECT 1 FROM user_mfa_recovery_codes)
              OR EXISTS (
                SELECT 1 FROM user_sessions WHERE ip_address IS NOT NULL OR user_agent IS NOT NULL
            ) OR EXISTS (
                SELECT 1
                FROM role_permissions rp
                JOIN roles r ON r.id = rp.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE p.code IN ('sessions.manage', 'users.password_reset')
                  AND r.code <> 'administrator'
            )
            """
        )
    ).scalar_one()
    if protected_data_exists:
        raise RuntimeError(
            "Identity-Security-Downgrade abgelehnt: MFA-, Passwort- oder Sitzungsdaten zuerst sichern."
        )

    uuid = postgresql.UUID(as_uuid=True)
    permission_ids = [stable_id("permission", code) for code in PERMISSIONS]
    role_permissions = sa.table("role_permissions", sa.column("permission_id", uuid))
    permissions = sa.table("permissions", sa.column("id", uuid))
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_user_mfa_recovery_codes_user_id", table_name="user_mfa_recovery_codes")
    op.drop_table("user_mfa_recovery_codes")
    op.drop_column("user_sessions", "user_agent")
    op.drop_column("user_sessions", "ip_address")
    op.drop_constraint("ck_users_mfa_secret", "users", type_="check")
    op.drop_column("users", "force_password_change")
    op.drop_column("users", "mfa_last_counter")
    op.drop_column("users", "mfa_secret_encrypted")
    op.drop_column("users", "mfa_enabled")
