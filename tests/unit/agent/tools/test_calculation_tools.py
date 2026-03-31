"""Unit tests for calculation tools."""

import pytest

from backend.app.agent.tools.calculation_tools import (
    _assess_risk_matrix,
    _calculate_roi,
    _calculate_weighted_score,
    _estimate_timeline,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# calculate_roi
# ---------------------------------------------------------------------------


class TestCalculateROI:
    def test_profitable_deal(self):
        result = _calculate_roi(50000, 35000, 6)
        assert result["profit"] == 15000
        assert result["margin_pct"] == 30.0
        assert result["profitability_rating"] == "high"
        assert result["break_even_months"] is not None
        assert result["break_even_months"] == pytest.approx(4.2, abs=0.1)

    def test_medium_margin(self):
        result = _calculate_roi(10000, 8000, 4)
        assert result["profit"] == 2000
        assert result["margin_pct"] == 20.0
        assert result["profitability_rating"] == "medium"

    def test_low_margin(self):
        result = _calculate_roi(10000, 9500, 3)
        assert result["profit"] == 500
        assert result["margin_pct"] == 5.0
        assert result["profitability_rating"] == "low"

    def test_loss_deal(self):
        result = _calculate_roi(10000, 15000, 6)
        assert result["profit"] == -5000
        assert result["margin_pct"] < 0
        assert result["profitability_rating"] == "loss"

    def test_zero_contract_amount(self):
        result = _calculate_roi(0, 5000, 3)
        assert result["margin_pct"] == 0.0
        assert result["break_even_months"] is None

    def test_zero_cost(self):
        result = _calculate_roi(10000, 0, 3)
        assert result["profit"] == 10000
        assert result["roi_pct"] == 0.0

    def test_zero_duration(self):
        result = _calculate_roi(10000, 5000, 0)
        assert result["monthly_revenue"] == 0.0
        assert result["break_even_months"] is None


# ---------------------------------------------------------------------------
# calculate_weighted_score
# ---------------------------------------------------------------------------


class TestCalculateWeightedScore:
    def test_standard_seven_criteria(self):
        scores = [
            {"criterion": "기술 적합성", "score": 80, "weight": 0.20},
            {"criterion": "수익성", "score": 70, "weight": 0.20},
            {"criterion": "리소스 가용성", "score": 60, "weight": 0.15},
            {"criterion": "일정 리스크", "score": 75, "weight": 0.15},
            {"criterion": "고객 리스크", "score": 65, "weight": 0.10},
            {"criterion": "요구사항 명확성", "score": 85, "weight": 0.10},
            {"criterion": "전략적 가치", "score": 90, "weight": 0.10},
        ]
        result = _calculate_weighted_score(scores)
        assert result["weight_sum"] == pytest.approx(1.0, abs=0.001)
        assert result["total_score"] == pytest.approx(74.25, abs=0.01)
        assert result["verdict"] == "go"
        assert len(result["scores"]) == 7

    def test_conditional_go_verdict(self):
        scores = [{"criterion": "test", "score": 50, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["total_score"] == 50.0
        assert result["verdict"] == "conditional_go"

    def test_no_go_verdict(self):
        scores = [{"criterion": "test", "score": 30, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["total_score"] == 30.0
        assert result["verdict"] == "no_go"

    def test_go_boundary(self):
        scores = [{"criterion": "test", "score": 70, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["verdict"] == "go"

    def test_conditional_go_boundary(self):
        scores = [{"criterion": "test", "score": 40, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["verdict"] == "conditional_go"

    def test_empty_scores(self):
        result = _calculate_weighted_score([])
        assert result["total_score"] == 0.0
        assert result["verdict"] == "no_go"
        assert result["scores"] == []

    def test_score_clamping(self):
        scores = [{"criterion": "test", "score": 150, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["scores"][0]["score"] == 100.0

    def test_weight_clamping(self):
        scores = [{"criterion": "test", "score": 80, "weight": 2.0}]
        result = _calculate_weighted_score(scores)
        assert result["scores"][0]["weight"] == 1.0

    def test_negative_score_clamped(self):
        scores = [{"criterion": "test", "score": -10, "weight": 1.0}]
        result = _calculate_weighted_score(scores)
        assert result["scores"][0]["score"] == 0.0

    def test_weights_not_summing_to_one(self):
        scores = [
            {"criterion": "a", "score": 80, "weight": 0.3},
            {"criterion": "b", "score": 60, "weight": 0.3},
        ]
        result = _calculate_weighted_score(scores)
        assert result["weight_sum"] == pytest.approx(0.6, abs=0.001)
        assert result["total_score"] == pytest.approx(42.0, abs=0.01)


# ---------------------------------------------------------------------------
# estimate_timeline
# ---------------------------------------------------------------------------


class TestEstimateTimeline:
    def test_medium_complexity_baseline(self):
        result = _estimate_timeline(6, 3, "medium")
        assert result["expected_months"] == 6.0
        assert result["optimistic_months"] < result["expected_months"]
        assert result["pessimistic_months"] > result["expected_months"]
        assert result["recommended_months"] > result["pert_estimate_months"]

    def test_low_complexity(self):
        result = _estimate_timeline(6, 3, "low")
        assert result["expected_months"] == pytest.approx(5.4, abs=0.1)
        assert result["factors"]["complexity_multiplier"] == 0.9

    def test_high_complexity(self):
        result = _estimate_timeline(6, 3, "high")
        assert result["expected_months"] == pytest.approx(7.8, abs=0.1)
        assert result["factors"]["complexity_multiplier"] == 1.3

    def test_large_team_brooks_overhead(self):
        result = _estimate_timeline(6, 8, "medium")
        assert result["factors"]["overhead_factor"] == pytest.approx(1.15, abs=0.001)
        assert result["expected_months"] > 6.0

    def test_team_of_five_no_overhead(self):
        result = _estimate_timeline(6, 5, "medium")
        assert result["factors"]["overhead_factor"] == 1.0

    def test_external_dependencies(self):
        result = _estimate_timeline(6, 3, "medium", has_external_dependencies=True)
        assert result["factors"]["external_dependency_factor"] == 1.15
        assert result["expected_months"] == pytest.approx(6.9, abs=0.1)

    def test_pert_buffer_is_twenty_percent(self):
        result = _estimate_timeline(10, 3, "medium")
        assert result["buffer_months"] == pytest.approx(result["pert_estimate_months"] * 0.2, abs=0.1)

    def test_recommended_includes_buffer(self):
        result = _estimate_timeline(6, 3, "medium")
        assert result["recommended_months"] == pytest.approx(
            result["pert_estimate_months"] + result["buffer_months"],
            abs=0.1,
        )

    def test_unknown_complexity_defaults_to_medium(self):
        result = _estimate_timeline(6, 3, "unknown")
        expected_medium = _estimate_timeline(6, 3, "medium")
        assert result["expected_months"] == expected_medium["expected_months"]


# ---------------------------------------------------------------------------
# assess_risk_matrix
# ---------------------------------------------------------------------------


class TestAssessRiskMatrix:
    def test_critical_risk(self):
        risks = [{"category": "technical", "item": "New tech", "probability": "HIGH", "impact": "HIGH"}]
        result = _assess_risk_matrix(risks)
        assert result["risks"][0]["level"] == "CRITICAL"
        assert result["summary"]["level_distribution"]["CRITICAL"] == 1

    def test_high_risk_combinations(self):
        risks = [
            {"category": "a", "item": "x", "probability": "HIGH", "impact": "MEDIUM"},
            {"category": "b", "item": "y", "probability": "MEDIUM", "impact": "HIGH"},
        ]
        result = _assess_risk_matrix(risks)
        assert all(r["level"] == "HIGH" for r in result["risks"])

    def test_medium_risk_combinations(self):
        risks = [
            {"category": "a", "item": "x", "probability": "HIGH", "impact": "LOW"},
            {"category": "b", "item": "y", "probability": "MEDIUM", "impact": "MEDIUM"},
            {"category": "c", "item": "z", "probability": "LOW", "impact": "HIGH"},
        ]
        result = _assess_risk_matrix(risks)
        assert all(r["level"] == "MEDIUM" for r in result["risks"])

    def test_low_risk_combinations(self):
        risks = [
            {"category": "a", "item": "x", "probability": "MEDIUM", "impact": "LOW"},
            {"category": "b", "item": "y", "probability": "LOW", "impact": "MEDIUM"},
            {"category": "c", "item": "z", "probability": "LOW", "impact": "LOW"},
        ]
        result = _assess_risk_matrix(risks)
        assert all(r["level"] == "LOW" for r in result["risks"])

    def test_empty_risks(self):
        result = _assess_risk_matrix([])
        assert result["risks"] == []
        assert result["summary"]["total_risks"] == 0
        assert result["summary"]["overall_risk_profile"] == "low"

    def test_overall_profile_very_high(self):
        risks = [
            {"category": "a", "item": "x", "probability": "HIGH", "impact": "HIGH"},
            {"category": "b", "item": "y", "probability": "HIGH", "impact": "HIGH"},
        ]
        result = _assess_risk_matrix(risks)
        assert result["summary"]["overall_risk_profile"] == "very_high"
        assert result["summary"]["average_score"] == 4.0

    def test_overall_profile_medium(self):
        risks = [
            {"category": "a", "item": "x", "probability": "MEDIUM", "impact": "MEDIUM"},
            {"category": "b", "item": "y", "probability": "MEDIUM", "impact": "MEDIUM"},
        ]
        result = _assess_risk_matrix(risks)
        assert result["summary"]["overall_risk_profile"] == "medium"
        assert result["summary"]["average_score"] == 2.0

    def test_mixed_risk_profile(self):
        risks = [
            {"category": "a", "item": "x", "probability": "HIGH", "impact": "HIGH"},
            {"category": "b", "item": "y", "probability": "LOW", "impact": "LOW"},
        ]
        result = _assess_risk_matrix(risks)
        # (4 + 1) / 2 = 2.5
        assert result["summary"]["average_score"] == 2.5
        assert result["summary"]["overall_risk_profile"] == "high"

    def test_case_insensitive_probability_impact(self):
        risks = [{"category": "a", "item": "x", "probability": "high", "impact": "high"}]
        result = _assess_risk_matrix(risks)
        assert result["risks"][0]["level"] == "CRITICAL"

    def test_defaults_when_missing_fields(self):
        risks = [{"category": "a", "item": "x"}]
        result = _assess_risk_matrix(risks)
        # Defaults to MEDIUM/MEDIUM
        assert result["risks"][0]["level"] == "MEDIUM"
