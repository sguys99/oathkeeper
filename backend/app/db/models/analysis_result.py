import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, JsonType


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    __table_args__ = (
        CheckConstraint(
            "verdict IN ('go', 'conditional_go', 'no_go', 'pending')",
            name="ck_analysis_results_verdict",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    total_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(20), nullable=True)
    scores: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    resource_estimate: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    risks: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    risk_interdependencies: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    similar_projects: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    report_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notion_saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    deal: Mapped["Deal"] = relationship(  # noqa: F821
        back_populates="analysis_result",
        lazy="selectin",
    )
