"""add_unique_notion_page_id

Revision ID: a3f1e9c72b54
Revises: 1c82bdc00d7c
Create Date: 2026-03-15 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f1e9c72b54"
down_revision: str | Sequence[str] | None = "1c82bdc00d7c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove duplicate deals by notion_page_id, then add partial unique index."""
    # Step 1: Delete duplicate deals, keeping the one with an analysis result
    # (or the most recently created one if none have results).
    op.execute(
        sa.text("""
        DELETE FROM deals
        WHERE id IN (
            SELECT d.id
            FROM deals d
            LEFT JOIN analysis_results ar ON ar.deal_id = d.id
            WHERE d.notion_page_id IS NOT NULL
              AND d.id NOT IN (
                  SELECT DISTINCT ON (d2.notion_page_id) d2.id
                  FROM deals d2
                  LEFT JOIN analysis_results ar2 ON ar2.deal_id = d2.id
                  WHERE d2.notion_page_id IS NOT NULL
                  ORDER BY d2.notion_page_id,
                           CASE WHEN ar2.id IS NOT NULL THEN 0 ELSE 1 END,
                           d2.created_at DESC
              )
        )
    """),
    )

    # Step 2: Add partial unique index (NULLs are allowed to have duplicates)
    op.create_index(
        "uq_deals_notion_page_id",
        "deals",
        ["notion_page_id"],
        unique=True,
        postgresql_where=sa.text("notion_page_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Drop the unique index."""
    op.drop_index("uq_deals_notion_page_id", table_name="deals")
