"""Shared utilities for LangGraph agent nodes."""

import json
import logging
import re
import uuid
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agent.llm import get_llm

logger = logging.getLogger(__name__)

MISSING_FIELDS_THRESHOLD = 3

CRITICAL_FIELDS = frozenset(
    {
        "customer_name",
        "customer_industry",
        "project_overview",
        "tech_requirements",
        "expected_amount",
        "duration_months",
    },
)


# ── LLM helpers ────────────────────────────────────────────────────────


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    llm=None,
) -> str:
    """Invoke the LLM with a system/user message pair and return the text."""
    if llm is None:
        llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = await llm.ainvoke(messages)
    return response.content


async def logged_call_llm(
    system_prompt: str,
    user_prompt: str,
    *,
    deal_id: uuid.UUID,
    node_name: str,
    llm=None,
) -> tuple[str, uuid.UUID]:
    """Invoke the LLM with logging. Returns (raw_output, log_id).

    Uses an independent DB session to avoid contention with parallel nodes.
    """
    from backend.app.db.repositories import agent_log_repo
    from backend.app.db.session import AsyncSessionLocal

    started_at = datetime.now(UTC)
    raw_output: str | None = None
    error_msg: str | None = None
    log_id = uuid.uuid4()

    try:
        raw_output = await call_llm(system_prompt, user_prompt, llm=llm)
    except Exception as exc:
        error_msg = str(exc)
        raise
    finally:
        completed_at = datetime.now(UTC)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        try:
            async with AsyncSessionLocal() as log_session:
                log = await agent_log_repo.create(
                    log_session,
                    deal_id=deal_id,
                    node_name=node_name,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    raw_output=raw_output,
                    error=error_msg,
                    duration_ms=duration_ms,
                    started_at=started_at,
                    completed_at=completed_at,
                )
                log_id = log.id
                await log_session.commit()
        except Exception:
            logger.exception("Failed to persist agent log for node=%s", node_name)

    return raw_output, log_id


async def update_log_parsed_output(log_id: uuid.UUID, parsed_output: dict | None) -> None:
    """Update parsed_output on an existing AgentLog using an independent session."""
    from backend.app.db.repositories import agent_log_repo
    from backend.app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            await agent_log_repo.update_parsed_output(session, log_id, parsed_output)
            await session.commit()
    except Exception:
        logger.exception("Failed to update parsed_output for log_id=%s", log_id)


async def log_node_skip(
    *,
    deal_id: uuid.UUID,
    node_name: str,
    reason: str,
    error: str | None = None,
) -> None:
    """Create an AgentLog entry for a node that completed without an LLM call."""
    from backend.app.db.repositories import agent_log_repo
    from backend.app.db.session import AsyncSessionLocal

    now = datetime.now(UTC)
    try:
        async with AsyncSessionLocal() as session:
            await agent_log_repo.create(
                session,
                deal_id=deal_id,
                node_name=node_name,
                parsed_output={"skipped": True, "reason": reason},
                error=error,
                duration_ms=0,
                started_at=now,
                completed_at=now,
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to persist skip log for node=%s", node_name)


def parse_json_response(content: str) -> dict:
    """Extract a JSON object from an LLM response string.

    Tries direct ``json.loads`` first, then falls back to extracting the
    first JSON code-fence block (`` ```json ... ``` ``).
    """
    # 1) Direct parse
    stripped = content.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 2) Code-fence extraction
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse JSON from LLM response: {stripped[:200]}...")


# ── Formatting helpers ─────────────────────────────────────────────────


def format_scoring_criteria(criteria) -> list[dict]:
    """Convert ScoringCriteria ORM objects to plain dicts for prompt rendering."""
    return [
        {
            "name": c.name,
            "weight": float(c.weight),
            "description": c.description or "",
        }
        for c in criteria
    ]


def format_team_members(members) -> list[dict]:
    """Convert TeamMember ORM objects to plain dicts for prompt rendering."""
    return [
        {
            "name": m.name,
            "role": m.role,
            "monthly_rate": m.monthly_rate,
            "is_available": m.is_available,
            "current_project": m.current_project,
            "available_from": str(m.available_from) if m.available_from else None,
        }
        for m in members
    ]


def format_company_context(results: list[dict]) -> str:
    """Format vector-store query results into a single string for prompts."""
    if not results:
        return ""
    sections = []
    for item in results:
        sections.append(f"[{item.get('type', 'general')}] {item.get('content', '')}")
    return "\n\n".join(sections)


async def fetch_company_settings(db) -> dict[str, str]:
    """Fetch business_direction, deal_criteria, short_term_strategy from DB."""
    from backend.app.db.repositories import settings_repo

    keys = ["business_direction", "deal_criteria", "short_term_strategy"]
    result: dict[str, str] = {}
    for key in keys:
        setting = await settings_repo.get_setting(db, key)
        result[key] = setting.value if setting else ""
    return result


def build_company_context(vector_context: str, company_settings: dict[str, str]) -> str:
    """Combine vector store context with DB company settings into a unified string."""
    parts: list[str] = []
    if company_settings.get("business_direction"):
        parts.append(f"[사업 방향] {company_settings['business_direction']}")
    if company_settings.get("short_term_strategy"):
        parts.append(f"[단기 전략] {company_settings['short_term_strategy']}")
    if vector_context:
        parts.append(vector_context)
    return "\n\n".join(parts)


# ── Business logic (shared by nodes and workers) ─────────────────────


_UNIT_TO_MANWON: dict[str, float] = {
    "원": 1 / 10_000,
    "만원": 1,
    "억원": 10_000,
}


def normalize_amount_to_manwon(structured: dict) -> dict:
    """Convert expected_amount to 만원 units and pin amount_unit = '만원'.

    Eliminates downstream LLM unit-conversion errors by normalizing at the
    code level immediately after deal structuring.
    """
    amount = structured.get("expected_amount")
    unit = structured.get("amount_unit", "만원")
    if amount is None:
        return structured
    factor = _UNIT_TO_MANWON.get(unit, 1)
    return {**structured, "expected_amount": round(amount * factor), "amount_unit": "만원"}


def recalculate_scores(scores: list[dict]) -> tuple[list[dict], float]:
    """Recompute weighted_score and total from LLM-provided raw scores."""
    recalculated = []
    total = 0.0
    for s in scores:
        score = float(s.get("score", 0))
        weight = float(s.get("weight", 0))
        weighted = round(score * weight, 2)
        total += weighted
        recalculated.append(
            {
                "criterion": s.get("criterion", ""),
                "score": score,
                "weight": weight,
                "weighted_score": weighted,
                "rationale": s.get("rationale", ""),
            },
        )
    return recalculated, round(total, 2)


def determine_verdict(total_score: float) -> str:
    """Server-side verdict based on score thresholds (don't trust LLM arithmetic)."""
    if total_score >= 70:
        return "go"
    if total_score >= 40:
        return "conditional_go"
    return "no_go"
