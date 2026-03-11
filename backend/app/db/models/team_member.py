import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin


class TeamMember(Base, TimestampMixin):
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    monthly_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    current_project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
