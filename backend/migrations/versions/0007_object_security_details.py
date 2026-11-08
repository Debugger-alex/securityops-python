"""Separate sensitive object security details behind dedicated permissions."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_object_security_details"
down_revision: str | None = "0006_object_assignments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    ("objects.sensitive.read", "Sicherheits- und Zutrittsdaten zugewiesener Objekte anzeigen"),
    ("objects.sensitive.manage", "Sicherheits- und Zutrittsdaten zugewiesener Objekte verwalten"),
]

ROLE_PERMISSIONS = {
    "administrator": {"objects.sensitive.read", "objects.sensitive.manage"},
    "management": {"objects.sensitive.read", "objects.sensitive.manage"},
    "operations": {"objects.sensitive.read", "objects.sensitive.manage"},
    "object_manager": {"objects.sensitive.read"},
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "object_security_details",
        sa.Column(
            "object_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("objects.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("security_requirements", sa.Text(), nullable=True),
        sa.Column("access_information", sa.Text(), nullable=True),
        sa.Column("emergency_contact", sa.String(200), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "security_requirements IS NULL OR length(trim(security_requirements)) > 0",
            name="ck_object_security_requirements_nonblank",
        ),
        sa.CheckConstraint(
            "access_information IS NULL OR length(trim(access_information)) > 0",
            name="ck_object_access_information_nonblank",
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO object_security_details (
                object_id, security_requirements, access_information, emergency_contact, updated_at
            )
            SELECT
                id,
                NULLIF(trim(security_requirements), ''),
                NULLIF(trim(access_information), ''),
                NULLIF(trim(emergency_contact), ''),
                updated_at
            FROM objects
            WHERE security_requirements IS NOT NULL
               OR access_information IS NOT NULL
               OR emergency_contact IS NOT NULL
            """
        )
    )
    op.drop_column("objects", "security_requirements")
    op.drop_column("objects", "access_information")
    op.drop_column("objects", "emergency_contact")

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
    op.add_column(
        "objects",
        sa.Column("security_requirements", sa.Text(), nullable=True),
    )
    op.add_column(
        "objects",
        sa.Column("access_information", sa.Text(), nullable=True),
    )
    op.add_column(
        "objects",
        sa.Column("emergency_contact", sa.String(200), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE objects
            SET security_requirements = details.security_requirements,
                access_information = details.access_information,
                emergency_contact = details.emergency_contact
            FROM object_security_details AS details
            WHERE details.object_id = objects.id
            """
        )
    )

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
    op.drop_table("object_security_details")
