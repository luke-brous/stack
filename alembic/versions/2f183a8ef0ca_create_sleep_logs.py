"""create sleep logs

Revision ID: 2f183a8ef0ca
Revises: 4003b1ca6f25
Create Date: 2026-09-29 11:39:11.598999

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f183a8ef0ca"
down_revision: str | Sequence[str] | None = "4003b1ca6f25"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sleep_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hours_slept", sa.Float(), nullable=False),
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
    op.drop_table("sleep_logs")
