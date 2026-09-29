"""create weight logs

Revision ID: 7facfd8ffdb1
Revises: 0ed5c8921e55
Create Date: 2026-09-22 12:07:34.680126

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7facfd8ffdb1"
down_revision: str | Sequence[str] | None = "0ed5c8921e55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "weight_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weight_lbs", sa.Float(), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("log_date"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("weight_logs")
