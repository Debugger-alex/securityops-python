"""Add customer website and contract status."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_customer_fields"
down_revision: str | None = "0009_personnel_links_docs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column("website", sa.String(length=2048), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column(
            "contract_status",
            sa.String(length=20),
            server_default="none",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_customers_contract_status",
        "customers",
        "contract_status IN ('none', 'draft', 'active', 'expired', 'terminated')",
    )
    op.alter_column("customers", "contract_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_customers_contract_status", "customers", type_="check")
    op.drop_column("customers", "contract_status")
    op.drop_column("customers", "website")
