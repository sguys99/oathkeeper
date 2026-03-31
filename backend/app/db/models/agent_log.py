import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, JsonType


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_name: Mapped[str] = mapped_column(String(50), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_output: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Hierarchical logging fields (Phase 5)
    parent_log_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    step_type: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )
    step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    worker_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    deal: Mapped["Deal"] = relationship(lazy="selectin")  # noqa: F821
    parent: Mapped["AgentLog | None"] = relationship(
        "AgentLog",
        remote_side="AgentLog.id",
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[list["AgentLog"]] = relationship(
        "AgentLog",
        back_populates="parent",
        lazy="selectin",
    )
