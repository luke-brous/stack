"""create protein logs

Revision ID: 8839ab54f0cb
Revises: 7facfd8ffdb1
Create Date: 2026-09-22 15:08:37.831565

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8839ab54f0cb"
down_revision: str | Sequence[str] | None = "7facfd8ffdb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "protein_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hit_goal", sa.Boolean(), nullable=False),
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
    op.drop_table("protein_logs")
