"""add error_message column to deals

Revision ID: c4a2f8d31e07
Revises: b7c3a1d5e890
Create Date: 2026-03-24 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a2f8d31e07"
down_revision: str | Sequence[str] | None = "b7c3a1d5e890"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "deals",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("deals", "error_message")
