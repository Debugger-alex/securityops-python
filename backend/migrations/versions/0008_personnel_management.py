"""Add employee records, protected personal details, and qualifications."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_personnel_management"
down_revision: str | None = "0007_object_security_details"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = [
    ("employees.sensitive.read", "Sensible Personaldaten anzeigen"),
    ("employees.sensitive.manage", "Sensible Personaldaten verwalten"),
    ("employees.absences.read", "Mitarbeiterabwesenheiten anzeigen"),
    ("employees.absences.manage", "Mitarbeiterabwesenheiten verwalten"),
]


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_number", sa.String(40), nullable=False, unique=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
        ),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("job_title", sa.String(120), nullable=True),
        sa.Column("employment_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("hired_on", sa.Date(), nullable=False),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("contract_type", sa.String(80), nullable=True),
        sa.Column("weekly_hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "employment_status IN ('active', 'inactive', 'leave', 'terminated')",
            name="ck_employees_employment_status",
        ),
        sa.CheckConstraint("length(trim(employee_number)) > 0", name="ck_employees_number"),
        sa.CheckConstraint("length(trim(full_name)) > 0", name="ck_employees_full_name"),
        sa.CheckConstraint(
            "weekly_hours IS NULL OR (weekly_hours > 0 AND weekly_hours <= 168)",
            name="ck_employees_weekly_hours",
        ),
        sa.CheckConstraint(
            "ended_on IS NULL OR ended_on >= hired_on", name="ck_employees_end_date"
        ),
    )
    op.create_index("ix_employees_status_name", "employees", ["employment_status", "full_name"])

    op.create_table(
        "employee_qualifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("issuer", sa.String(160), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_employee_qualifications_name"),
        sa.CheckConstraint(
            "expires_on IS NULL OR valid_from IS NULL OR expires_on >= valid_from",
            name="ck_employee_qualifications_dates",
        ),
    )
    op.create_index(
        "ix_employee_qualifications_expiry",
        "employee_qualifications",
        ["expires_on", "archived_at"],
    )
    op.create_index(
        "ix_employee_qualifications_employee",
        "employee_qualifications",
        ["employee_id", "expires_on"],
    )

    op.create_table(
        "employee_absences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("absence_type", sa.String(20), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_by_id",
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "absence_type IN ('vacation', 'sick_leave', 'other')",
            name="ck_employee_absences_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_employee_absences_status",
        ),
        sa.CheckConstraint("ends_on >= starts_on", name="ck_employee_absences_dates"),
    )
    op.create_index(
        "ix_employee_absences_employee_dates",
        "employee_absences",
        ["employee_id", "starts_on", "ends_on"],
    )

    op.create_table(
        "employee_sensitive_details",
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("emergency_contact", sa.String(300), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "address IS NULL OR length(trim(address)) > 0",
            name="ck_employee_sensitive_address",
        ),
        sa.CheckConstraint(
            "emergency_contact IS NULL OR length(trim(emergency_contact)) > 0",
            name="ck_employee_sensitive_emergency_contact",
        ),
    )

    op.create_table(
        "employee_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="RESTRICT"),
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
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_employee_history_employee_created", "employee_history", ["employee_id", "created_at"]
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
    op.drop_index("ix_employee_history_employee_created", table_name="employee_history")
    op.drop_table("employee_history")
    op.drop_table("employee_sensitive_details")
    op.drop_index("ix_employee_absences_employee_dates", table_name="employee_absences")
    op.drop_table("employee_absences")
    op.drop_index("ix_employee_qualifications_employee", table_name="employee_qualifications")
    op.drop_index("ix_employee_qualifications_expiry", table_name="employee_qualifications")
    op.drop_table("employee_qualifications")
    op.drop_index("ix_employees_status_name", table_name="employees")
    op.drop_table("employees")
