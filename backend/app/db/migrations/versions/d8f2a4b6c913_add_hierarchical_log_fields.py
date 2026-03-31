"""add hierarchical log fields to agent_logs

Revision ID: d8f2a4b6c913
Revises: c4a2f8d31e07
Create Date: 2026-03-31 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8f2a4b6c913"
down_revision: str | Sequence[str] | None = "c4a2f8d31e07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add hierarchical logging columns to agent_logs."""
    op.add_column(
        "agent_logs",
        sa.Column("parent_log_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "agent_logs",
        sa.Column("step_type", sa.String(30), nullable=True),
    )
    op.add_column(
        "agent_logs",
        sa.Column("step_index", sa.Integer(), nullable=True),
    )
    op.add_column(
        "agent_logs",
        sa.Column("tool_name", sa.String(100), nullable=True),
    )
    op.add_column(
        "agent_logs",
        sa.Column("worker_name", sa.String(50), nullable=True),
    )
    op.create_foreign_key(
        "fk_agent_logs_parent",
        "agent_logs",
        "agent_logs",
        ["parent_log_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_agent_logs_parent_log_id",
        "agent_logs",
        ["parent_log_id"],
    )
    op.create_index(
        "ix_agent_logs_step_type",
        "agent_logs",
        ["step_type"],
    )
    op.create_index(
        "ix_agent_logs_worker_name",
        "agent_logs",
        ["worker_name"],
    )


def downgrade() -> None:
    """Remove hierarchical logging columns from agent_logs."""
    op.drop_index("ix_agent_logs_worker_name", table_name="agent_logs")
    op.drop_index("ix_agent_logs_step_type", table_name="agent_logs")
    op.drop_index("ix_agent_logs_parent_log_id", table_name="agent_logs")
    op.drop_constraint(
        "fk_agent_logs_parent",
        "agent_logs",
        type_="foreignkey",
    )
    op.drop_column("agent_logs", "worker_name")
    op.drop_column("agent_logs", "tool_name")
    op.drop_column("agent_logs", "step_index")
    op.drop_column("agent_logs", "step_type")
    op.drop_column("agent_logs", "parent_log_id")
