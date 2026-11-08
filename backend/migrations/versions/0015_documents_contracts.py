"""Add private document management, contracts, and reminders."""

from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert as pg_insert

revision: str = "0015_documents_contracts"
down_revision: str | None = "0014_owks_wachbuch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSIONS = {
    "documents.read": "Dokumentmetadaten und Historie einsehen",
    "documents.create": "Dokumente hochladen und anlegen",
    "documents.update": "Dokumentmetadaten und Versionen ändern",
    "documents.archive": "Dokumente archivieren und reaktivieren",
    "documents.download": "Dokumentdateien geschützt herunterladen",
    "documents.approve": "Dokumentversionen freigeben",
    "contracts.read": "Verträge und Chronik einsehen",
    "contracts.create": "Verträge anlegen",
    "contracts.update": "Verträge bearbeiten",
    "contracts.archive": "Verträge archivieren und reaktivieren",
    "contracts.manage_reminders": "Erinnerungsfristen konfigurieren und Erinnerungen bearbeiten",
}


def stable_id(kind: str, code: str):
    return uuid5(NAMESPACE_URL, f"securityops:{kind}:{code}")


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_number", sa.String(80), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'expired', 'archived')", name="ck_documents_status"
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_documents_title"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_documents_status_expiry", "documents", ["status", "expires_on"])
    op.create_index("ix_documents_customer", "documents", ["customer_id", "archived_at"])
    op.create_index("ix_documents_object", "documents", ["object_id", "archived_at"])
    op.create_index("ix_documents_employee", "documents", ["employee_id", "archived_at"])

    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(32), nullable=False, unique=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("version > 0", name="ck_document_versions_version"),
        sa.CheckConstraint("size_bytes > 0", name="ck_document_versions_size"),
        sa.CheckConstraint(
            "media_type IN ('application/pdf', 'image/png', 'image/jpeg', "
            "'application/vnd.openxmlformats-officedocument.wordprocessingml.document', "
            "'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')",
            name="ck_document_versions_media_type",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("document_id", "version", name="uq_document_versions_number"),
    )
    op.create_index(
        "ix_document_versions_document_created", "document_versions", ["document_id", "created_at"]
    )

    op.create_table(
        "document_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')", name="ck_document_approvals_status"
        ),
        sa.ForeignKeyConstraint(["version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_document_approvals_version_created", "document_approvals", ["version_id", "created_at"]
    )

    op.create_table(
        "document_read_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "read_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["version_id"], ["document_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("version_id", "user_id", name="uq_document_read_receipt_user_version"),
    )
    op.create_index(
        "ix_document_read_receipts_version_read",
        "document_read_receipts",
        ["version_id", "read_at"],
    )

    op.create_table(
        "document_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_document_history_document_created", "document_history", ["document_id", "created_at"]
    )

    op.create_table(
        "contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_number", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("contract_type", sa.String(30), nullable=False),
        sa.Column("counterparty", sa.String(200), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("renewal_rule", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "contract_type IN ('customer', 'object', 'personnel', 'service', 'additional', 'other')",
            name="ck_contracts_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'terminated', 'expired', 'archived')",
            name="ck_contracts_status",
        ),
        sa.CheckConstraint("ends_on IS NULL OR ends_on >= starts_on", name="ck_contracts_dates"),
        sa.CheckConstraint(
            "notice_period_days IS NULL OR notice_period_days BETWEEN 0 AND 3650",
            name="ck_contracts_notice_period",
        ),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_contracts_name"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["object_id"], ["objects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_contracts_status_end", "contracts", ["status", "ends_on"])
    op.create_index("ix_contracts_customer", "contracts", ["customer_id", "archived_at"])
    op.create_index("ix_contracts_object", "contracts", ["object_id", "archived_at"])

    op.create_table(
        "contract_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_contract_history_contract_created", "contract_history", ["contract_id", "created_at"]
    )

    op.create_table(
        "document_contract_reminder_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_days", sa.JSON(), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("id = 1", name="ck_doc_contract_reminder_settings_singleton"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.execute(
        "INSERT INTO document_contract_reminder_settings (id, lead_days) "
        "VALUES (1, '[90, 60, 30, 14, 7]'::json)"
    )

    op.create_table(
        "document_contract_reminders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reminder_type", sa.String(30), nullable=False),
        sa.Column("event_on", sa.Date(), nullable=False),
        sa.Column("remind_on", sa.Date(), nullable=False),
        sa.Column("deduplication_key", sa.String(160), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "(document_id IS NOT NULL AND contract_id IS NULL) OR "
            "(document_id IS NULL AND contract_id IS NOT NULL)",
            name="ck_doc_contract_reminders_single_target",
        ),
        sa.CheckConstraint(
            "reminder_type IN ('document_expiry', 'contract_expiry', "
            "'contract_termination', 'contract_renewal')",
            name="ck_doc_contract_reminders_type",
        ),
        sa.CheckConstraint(
            "status IN ('open', 'completed', 'dismissed')", name="ck_doc_contract_reminders_status"
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_doc_contract_reminders_due_status",
        "document_contract_reminders",
        ["remind_on", "status"],
    )

    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String(100)),
        sa.column("description", sa.String(300)),
    )
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    connection = op.get_bind()
    connection.execute(
        pg_insert(permissions)
        .values(
            [
                {"id": stable_id("permission", code), "code": code, "description": description}
                for code, description in PERMISSIONS.items()
                if code != "documents.read"
            ]
        )
        .on_conflict_do_nothing()
    )
    all_document_permissions = set(PERMISSIONS)
    all_contract_permissions = {code for code in PERMISSIONS if code.startswith("contracts.")}
    document_management = {
        "documents.read",
        "documents.create",
        "documents.update",
        "documents.archive",
        "documents.download",
        "documents.approve",
    }
    matrix = {
        "administrator": all_document_permissions,
        "management": all_document_permissions,
        "administration": all_document_permissions,
        "accounting": {
            "documents.read",
            "documents.download",
            *all_contract_permissions,
        },
        "hr": {
            *document_management,
            *all_contract_permissions,
        },
        "operations": {
            "documents.read",
            "documents.create",
            "documents.update",
            "documents.download",
            "contracts.read",
        },
        "object_manager": {"documents.read", "documents.download"},
        "auditor": {"documents.read", "contracts.read"},
        "employee": {"documents.read", "documents.download"},
    }
    connection.execute(
        pg_insert(role_permissions)
        .values(
            [
                {
                    "role_id": stable_id("role", role_code),
                    "permission_id": stable_id("permission", permission_code),
                }
                for role_code, codes in matrix.items()
                for permission_code in sorted(codes)
            ]
        )
        .on_conflict_do_nothing()
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM documents)
                OR EXISTS (SELECT 1 FROM document_versions)
                OR EXISTS (SELECT 1 FROM document_approvals)
                OR EXISTS (SELECT 1 FROM document_read_receipts)
                OR EXISTS (SELECT 1 FROM document_history)
                OR EXISTS (SELECT 1 FROM contracts)
                OR EXISTS (SELECT 1 FROM contract_history)
                OR EXISTS (SELECT 1 FROM document_contract_reminders)
                OR EXISTS (
                    SELECT 1 FROM document_contract_reminder_settings
                    WHERE id <> 1
                        OR lead_days::jsonb <> '[90, 60, 30, 14, 7]'::jsonb
                        OR updated_by_id IS NOT NULL
                ) THEN
                RAISE EXCEPTION
                    'Dokumenten-/Vertrags-Downgrade abgelehnt: Fachdaten oder angepasste Erinnerungseinstellungen zuerst sichern';
            END IF;
        END
        $$
        """
    )
    permission_ids = [
        stable_id("permission", code) for code in PERMISSIONS if code != "documents.read"
    ]
    role_permissions = sa.table(
        "role_permissions",
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("permission_id", postgresql.UUID(as_uuid=True)),
    )
    permissions = sa.table(
        "permissions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
    )
    connection = op.get_bind()
    connection.execute(
        sa.delete(role_permissions).where(role_permissions.c.permission_id.in_(permission_ids))
    )
    connection.execute(
        sa.delete(role_permissions).where(
            role_permissions.c.role_id == stable_id("role", "accounting"),
            role_permissions.c.permission_id == stable_id("permission", "documents.read"),
        )
    )
    connection.execute(sa.delete(permissions).where(permissions.c.id.in_(permission_ids)))
    op.drop_index("ix_doc_contract_reminders_due_status", table_name="document_contract_reminders")
    op.drop_table("document_contract_reminders")
    connection.execute(sa.text("DELETE FROM document_contract_reminder_settings WHERE id = 1"))
    op.drop_table("document_contract_reminder_settings")
    op.drop_index("ix_contract_history_contract_created", table_name="contract_history")
    op.drop_table("contract_history")
    op.drop_index("ix_contracts_object", table_name="contracts")
    op.drop_index("ix_contracts_customer", table_name="contracts")
    op.drop_index("ix_contracts_status_end", table_name="contracts")
    op.drop_table("contracts")
    op.drop_index("ix_document_history_document_created", table_name="document_history")
    op.drop_table("document_history")
    op.drop_index("ix_document_read_receipts_version_read", table_name="document_read_receipts")
    op.drop_table("document_read_receipts")
    op.drop_index("ix_document_approvals_version_created", table_name="document_approvals")
    op.drop_table("document_approvals")
    op.drop_index("ix_document_versions_document_created", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index("ix_documents_employee", table_name="documents")
    op.drop_index("ix_documents_object", table_name="documents")
    op.drop_index("ix_documents_customer", table_name="documents")
    op.drop_index("ix_documents_status_expiry", table_name="documents")
    op.drop_table("documents")
