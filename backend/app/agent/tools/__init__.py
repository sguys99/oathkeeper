"""Agent tools — re-exports and categorized tool lists."""

from backend.app.agent.tools._context import get_tool_context, init_tool_context
from backend.app.agent.tools.calculation_tools import (
    assess_risk_matrix,
    calculate_roi,
    calculate_weighted_score,
    estimate_timeline,
)
from backend.app.agent.tools.data_tools import (
    get_company_settings,
    get_past_deal_analysis,
    get_scoring_criteria,
    get_team_members,
    search_company_context,
    search_similar_projects,
)
from backend.app.agent.tools.external_tools import fetch_notion_deal, web_search
from backend.app.agent.tools.utils_tools import current_date, format_currency

DATA_TOOLS = [
    search_similar_projects,
    search_company_context,
    get_team_members,
    get_scoring_criteria,
    get_company_settings,
    get_past_deal_analysis,
]

EXTERNAL_TOOLS = [web_search, fetch_notion_deal]

CALCULATION_TOOLS = [calculate_roi, calculate_weighted_score, estimate_timeline, assess_risk_matrix]

UTILITY_TOOLS = [format_currency, current_date]

ALL_TOOLS = DATA_TOOLS + EXTERNAL_TOOLS + CALCULATION_TOOLS + UTILITY_TOOLS

__all__ = [
    "ALL_TOOLS",
    "CALCULATION_TOOLS",
    "DATA_TOOLS",
    "EXTERNAL_TOOLS",
    "UTILITY_TOOLS",
    "assess_risk_matrix",
    "calculate_roi",
    "calculate_weighted_score",
    "current_date",
    "estimate_timeline",
    "fetch_notion_deal",
    "format_currency",
    "get_company_settings",
    "get_past_deal_analysis",
    "get_scoring_criteria",
    "get_team_members",
    "get_tool_context",
    "init_tool_context",
    "search_company_context",
    "search_similar_projects",
    "web_search",
]
