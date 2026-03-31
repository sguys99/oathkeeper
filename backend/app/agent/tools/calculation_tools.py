"""Calculation tools — deterministic arithmetic the LLM should not guess."""

import json
import logging

from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# calculate_roi
# ---------------------------------------------------------------------------


class CalculateROIInput(BaseModel):
    """Calculate ROI and profitability metrics."""

    contract_amount: int = Field(description="Total contract amount (만원)")
    estimated_cost: int = Field(description="Total estimated cost (만원)")
    duration_months: float = Field(description="Project duration in months")


def _calculate_roi(
    contract_amount: int,
    estimated_cost: int,
    duration_months: float,
) -> dict:
    profit = contract_amount - estimated_cost
    margin_pct = (profit / contract_amount * 100) if contract_amount > 0 else 0.0
    roi_pct = (profit / estimated_cost * 100) if estimated_cost > 0 else 0.0

    monthly_revenue = contract_amount / duration_months if duration_months > 0 else 0.0
    monthly_cost = estimated_cost / duration_months if duration_months > 0 else 0.0
    break_even_months = (estimated_cost / monthly_revenue) if monthly_revenue > 0 else None

    if margin_pct >= 30:
        rating = "high"
    elif margin_pct >= 15:
        rating = "medium"
    elif margin_pct >= 0:
        rating = "low"
    else:
        rating = "loss"

    return {
        "contract_amount": contract_amount,
        "estimated_cost": estimated_cost,
        "profit": profit,
        "margin_pct": round(margin_pct, 2),
        "roi_pct": round(roi_pct, 2),
        "monthly_revenue": round(monthly_revenue, 2),
        "monthly_cost": round(monthly_cost, 2),
        "break_even_months": round(break_even_months, 1) if break_even_months else None,
        "profitability_rating": rating,
        "duration_months": duration_months,
    }


@tool(args_schema=CalculateROIInput)
async def calculate_roi(
    contract_amount: int,
    estimated_cost: int,
    duration_months: float,
) -> str:
    """Calculate ROI, profit margin, break-even point, and monthly profitability.
    All amounts in 만원."""
    try:
        result = _calculate_roi(contract_amount, estimated_cost, duration_months)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.exception("calculate_roi failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# calculate_weighted_score
# ---------------------------------------------------------------------------


class CalculateWeightedScoreInput(BaseModel):
    """Calculate weighted score from individual criterion scores."""

    scores: list[dict] = Field(
        description='List of {"criterion": str, "score": 0-100, "weight": 0.0-1.0}',
    )


def _calculate_weighted_score(scores: list[dict]) -> dict:
    recalculated = []
    total = 0.0

    for s in scores:
        score = max(0.0, min(100.0, float(s.get("score", 0))))
        weight = max(0.0, min(1.0, float(s.get("weight", 0))))
        weighted = round(score * weight, 2)
        total += weighted
        recalculated.append(
            {
                "criterion": s.get("criterion", ""),
                "score": score,
                "weight": weight,
                "weighted_score": weighted,
            },
        )

    total = round(total, 2)

    if total >= 70:
        verdict = "go"
    elif total >= 40:
        verdict = "conditional_go"
    else:
        verdict = "no_go"

    return {
        "scores": recalculated,
        "total_score": total,
        "verdict": verdict,
        "weight_sum": round(sum(s["weight"] for s in recalculated), 3),
    }


@tool(args_schema=CalculateWeightedScoreInput)
async def calculate_weighted_score(scores: list[dict]) -> str:
    """Calculate weighted total score from individual criterion scores and weights.
    Returns per-criterion weighted scores, total, and verdict (go/conditional_go/no_go)."""
    try:
        result = _calculate_weighted_score(scores)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.exception("calculate_weighted_score failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# estimate_timeline
# ---------------------------------------------------------------------------

_COMPLEXITY_MULTIPLIERS = {"low": 0.9, "medium": 1.0, "high": 1.3}


class EstimateTimelineInput(BaseModel):
    """Estimate project timeline based on resources and scope."""

    base_duration_months: float = Field(description="Initial estimated duration in months")
    team_size: int = Field(description="Number of team members", ge=1)
    complexity: str = Field(description="Project complexity: low, medium, high")
    has_external_dependencies: bool = Field(
        default=False,
        description="Whether project has external dependencies",
    )


def _estimate_timeline(
    base_duration_months: float,
    team_size: int,
    complexity: str,
    has_external_dependencies: bool = False,
) -> dict:
    complexity_mult = _COMPLEXITY_MULTIPLIERS.get(complexity.lower(), 1.0)

    # Brooks's Law: communication overhead for teams > 5
    overhead_factor = 1.0
    if team_size > 5:
        overhead_factor = 1.0 + (team_size - 5) * 0.05

    ext_factor = 1.15 if has_external_dependencies else 1.0

    expected = base_duration_months * complexity_mult * overhead_factor * ext_factor
    optimistic = expected * 0.8
    pessimistic = expected * 1.4

    # PERT three-point estimation
    pert = (optimistic + 4 * expected + pessimistic) / 6
    buffer = pert * 0.2
    recommended = pert + buffer

    return {
        "base_duration_months": base_duration_months,
        "optimistic_months": round(optimistic, 1),
        "expected_months": round(expected, 1),
        "pessimistic_months": round(pessimistic, 1),
        "pert_estimate_months": round(pert, 1),
        "buffer_months": round(buffer, 1),
        "recommended_months": round(recommended, 1),
        "factors": {
            "complexity": complexity,
            "complexity_multiplier": complexity_mult,
            "team_size": team_size,
            "overhead_factor": round(overhead_factor, 3),
            "external_dependency_factor": ext_factor,
        },
    }


@tool(args_schema=EstimateTimelineInput)
async def estimate_timeline(
    base_duration_months: float,
    team_size: int,
    complexity: str,
    has_external_dependencies: bool = False,
) -> str:
    """Estimate realistic timeline with buffer, considering team size, complexity,
    and external dependencies. Returns optimistic, expected, and pessimistic estimates."""
    try:
        result = _estimate_timeline(
            base_duration_months,
            team_size,
            complexity,
            has_external_dependencies,
        )
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.exception("estimate_timeline failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# assess_risk_matrix
# ---------------------------------------------------------------------------

_RISK_MATRIX: dict[tuple[str, str], str] = {
    ("HIGH", "HIGH"): "CRITICAL",
    ("HIGH", "MEDIUM"): "HIGH",
    ("HIGH", "LOW"): "MEDIUM",
    ("MEDIUM", "HIGH"): "HIGH",
    ("MEDIUM", "MEDIUM"): "MEDIUM",
    ("MEDIUM", "LOW"): "LOW",
    ("LOW", "HIGH"): "MEDIUM",
    ("LOW", "MEDIUM"): "LOW",
    ("LOW", "LOW"): "LOW",
}

_LEVEL_SCORES = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


class RiskEntry(BaseModel):
    category: str = Field(description="Risk category")
    item: str = Field(description="Risk item name")
    probability: str = Field(description="HIGH, MEDIUM, or LOW")
    impact: str = Field(description="HIGH, MEDIUM, or LOW")


class AssessRiskMatrixInput(BaseModel):
    """Assess risk levels from probability and impact."""

    risks: list[RiskEntry] = Field(
        description="List of risks with probability and impact",
    )


def _assess_risk_matrix(risks: list[dict]) -> dict:
    assessed = []
    scores_sum = 0
    level_counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for risk in risks:
        prob = risk.get("probability", "MEDIUM").upper()
        impact = risk.get("impact", "MEDIUM").upper()
        level = _RISK_MATRIX.get((prob, impact), "MEDIUM")
        level_counts[level] += 1
        scores_sum += _LEVEL_SCORES[level]
        assessed.append(
            {
                "category": risk.get("category", ""),
                "item": risk.get("item", ""),
                "probability": prob,
                "impact": impact,
                "level": level,
            },
        )

    n = len(assessed) or 1
    avg_score = scores_sum / n

    if avg_score >= 3.0:
        overall = "very_high"
    elif avg_score >= 2.5:
        overall = "high"
    elif avg_score >= 1.5:
        overall = "medium"
    else:
        overall = "low"

    return {
        "risks": assessed,
        "summary": {
            "total_risks": len(assessed),
            "level_distribution": level_counts,
            "average_score": round(avg_score, 2),
            "overall_risk_profile": overall,
        },
    }


@tool(args_schema=AssessRiskMatrixInput)
async def assess_risk_matrix(risks: list[dict]) -> str:
    """Calculate risk levels from probability x impact matrix. Returns each risk with
    its computed level (CRITICAL, HIGH, MEDIUM, LOW) and a summary risk profile."""
    try:
        raw = [r.model_dump() if isinstance(r, BaseModel) else r for r in risks]
        result = _assess_risk_matrix(raw)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.exception("assess_risk_matrix failed")
        return json.dumps({"error": str(e)})
