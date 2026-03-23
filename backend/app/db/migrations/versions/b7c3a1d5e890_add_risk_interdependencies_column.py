"""add risk_interdependencies column to analysis_results

Revision ID: b7c3a1d5e890
Revises: 68b9b729885b
Create Date: 2026-03-23 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c3a1d5e890"
down_revision: str | Sequence[str] | None = "68b9b729885b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "analysis_results",
        sa.Column("risk_interdependencies", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("analysis_results", "risk_interdependencies")
