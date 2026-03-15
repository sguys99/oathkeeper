import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, JsonType, TimestampMixin


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'analyzing', 'completed', 'failed')",
            name="ck_deals_status",
        ),
        Index(
            "uq_deals_notion_page_id",
            "notion_page_id",
            unique=True,
            postgresql_where=text("notion_page_id IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    notion_page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    structured_data: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    creator: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="deals",
        lazy="selectin",
    )
    analysis_result: Mapped["AnalysisResult | None"] = relationship(  # noqa: F821
        back_populates="deal",
        uselist=False,
        lazy="selectin",
    )
