"""Shared utilities for LangGraph agent nodes."""

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agent.llm import get_llm

logger = logging.getLogger(__name__)

MISSING_FIELDS_THRESHOLD = 3


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
