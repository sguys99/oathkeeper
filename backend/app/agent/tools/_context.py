"""Tool dependency context — module-level registry for shared resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from backend.app.db.vector_store import CompanyContextStore, ProjectHistoryStore


@dataclass
class ToolContext:
    """Holds shared dependencies that tools need at runtime."""

    session_factory: async_sessionmaker
    company_context_store: CompanyContextStore
    project_history_store: ProjectHistoryStore


_context: ToolContext | None = None


def init_tool_context(
    session_factory: async_sessionmaker,
    company_context_store: CompanyContextStore,
    project_history_store: ProjectHistoryStore,
) -> None:
    """Initialize the module-level tool context. Call once at agent startup."""
    global _context
    _context = ToolContext(
        session_factory=session_factory,
        company_context_store=company_context_store,
        project_history_store=project_history_store,
    )


def get_tool_context() -> ToolContext:
    """Retrieve the tool context. Raises if not initialized."""
    if _context is None:
        raise RuntimeError(
            "Tool context not initialized. Call init_tool_context() before using tools.",
        )
    return _context
