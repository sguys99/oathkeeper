"""Orchestrator agent — top-level ReAct agent builder."""

import logging

from langgraph.prebuilt import create_react_agent

from backend.app.agent.llm import get_llm_uncached
from backend.app.agent.orchestrator.meta_tools import META_TOOLS
from backend.app.agent.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

ORCHESTRATOR_MAX_ITERATIONS = 12


def build_orchestrator(deal_id: str):
    """Build and return the compiled orchestrator agent.

    Parameters
    ----------
    deal_id : str
        Used to inject deal_id into the system prompt for clarity.

    Returns
    -------
    CompiledStateGraph
        A compiled LangGraph agent ready for .ainvoke() or .astream().
    """
    llm = get_llm_uncached(temperature=0.0, max_tokens=4096)
    tpl = load_prompt("orchestrator")
    prompt = tpl.render_system() + "\n\n" + tpl.render_user(deal_id=deal_id)

    return create_react_agent(
        model=llm,
        tools=META_TOOLS,
        prompt=prompt,
        name="orchestrator",
    )
