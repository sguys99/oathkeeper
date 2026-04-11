"""add workflow_type to analysis_results

Revision ID: e9a3b5d7f124
Revises: d8f2a4b6c913
Create Date: 2026-04-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9a3b5d7f124"
down_revision: str | Sequence[str] | None = "d8f2a4b6c913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add workflow_type column to analysis_results."""
    op.add_column(
        "analysis_results",
        sa.Column("workflow_type", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    """Remove workflow_type column from analysis_results."""
    op.drop_column("analysis_results", "workflow_type")
