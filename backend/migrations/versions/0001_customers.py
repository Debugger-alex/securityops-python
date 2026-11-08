"""Create initial customer table."""

from typing import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_customers"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("customer_number", sa.String(length=40), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("customer_number", name="uq_customers_customer_number"),
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'lead')", name="ck_customers_status"
        ),
        sa.CheckConstraint(
            "length(trim(company_name)) > 0", name="ck_customers_company_name"
        ),
    )
    op.create_index("ix_customers_customer_number", "customers", ["customer_number"])
    op.create_index("ix_customers_company_name", "customers", ["company_name"])
    op.create_index("ix_customers_status", "customers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_customers_status", table_name="customers")
    op.drop_index("ix_customers_company_name", table_name="customers")
    op.drop_index("ix_customers_customer_number", table_name="customers")
    op.drop_table("customers")
