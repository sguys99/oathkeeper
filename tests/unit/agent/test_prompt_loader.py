"""Tests for prompt loader and Jinja2 rendering."""

import pytest

from backend.app.agent.prompt_loader import (
    PromptNotFoundError,
    PromptTemplate,
    load_prompt,
    render_prompt,
)

pytestmark = pytest.mark.unit


class TestLoadPrompt:
    """Test YAML prompt loading."""

    def test_load_system_prompt(self):
        tpl = load_prompt("system")
        assert tpl.name == "system"
        assert tpl.version == "2.0"

    def test_load_deal_structuring(self):
        tpl = load_prompt("deal_structuring")
        assert tpl.name == "deal_structuring"
        assert tpl.output_schema is not None
        assert "customer_name" in str(tpl.output_schema)

    def test_load_scoring(self):
        tpl = load_prompt("scoring")
        assert tpl.output_schema is not None
        assert "scores" in tpl.output_schema["properties"]

    def test_load_resource_estimation(self):
        tpl = load_prompt("resource_estimation")
        assert tpl.output_schema is not None

    def test_load_risk_analysis(self):
        tpl = load_prompt("risk_analysis")
        assert tpl.output_schema is not None
        assert "risks" in tpl.output_schema["properties"]

    def test_load_similar_project(self):
        tpl = load_prompt("similar_project")
        assert tpl.output_schema is not None

    def test_load_final_verdict(self):
        tpl = load_prompt("final_verdict")
        assert tpl.name == "final_verdict"

    def test_load_nonexistent_raises_error(self):
        with pytest.raises(PromptNotFoundError, match="not found"):
            load_prompt("nonexistent_prompt")


class TestPromptRendering:
    """Test Jinja2 template rendering."""

    def test_system_prompt_with_context(self):
        tpl = load_prompt("system")
        rendered = tpl.render_system(
            company_context="AI 솔루션 전문 기업",
            deal_criteria="계약 금액 5000만원 이상",
        )
        assert "AI 솔루션 전문 기업" in rendered
        assert "계약 금액 5000만원 이상" in rendered
        assert "근거 기반 분석" in rendered
        assert "보수적 평가" in rendered

    def test_system_prompt_without_context(self):
        tpl = load_prompt("system")
        rendered = tpl.render_system()
        assert "컨텍스트가 제공되지 않았습니다" in rendered
        assert "분석 원칙" in rendered

    def test_deal_structuring_render(self):
        tpl = load_prompt("deal_structuring")
        rendered = tpl.render_user(
            deal_input="삼성전자에서 AI 챗봇 개발을 요청했습니다.",
        )
        assert "삼성전자" in rendered
        assert "customer_name" in rendered

    def test_scoring_render(self):
        tpl = load_prompt("scoring")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사", "project_summary": "AI 개발"},
            scoring_criteria=[
                {"name": "기술 적합성", "weight": 0.2, "description": "기술 스택 매칭"},
            ],
        )
        assert "customer_name" in rendered
        assert "기술 적합성" in rendered

    def test_resource_estimation_with_team(self):
        tpl = load_prompt("resource_estimation")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사"},
            team_members=[
                {
                    "name": "김개발",
                    "role": "Backend",
                    "monthly_rate": 800,
                    "is_available": True,
                    "current_project": None,
                },
            ],
        )
        assert "김개발" in rendered
        assert "Backend" in rendered
        assert "투입 가능" in rendered

    def test_risk_analysis_render(self):
        tpl = load_prompt("risk_analysis")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사"},
        )
        assert "customer_name" in rendered
        assert "risk_interdependencies" in rendered

    def test_final_verdict_render(self):
        tpl = load_prompt("final_verdict")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사"},
            total_score=75.0,
            verdict="go",
            scores=[
                {
                    "criterion": "기술 적합성",
                    "score": 80,
                    "weight": 0.2,
                    "rationale": "기술 스택 일치",
                },
            ],
            resource_estimate={
                "duration_months": 3,
                "duration_with_buffer": 3.6,
                "cost_breakdown": {
                    "labor_cost": 4000,
                    "overhead_cost": 1000,
                    "total_cost": 5000,
                    "cost_calculation": "PM 1명 x 1000만원 x 3개월",
                },
                "profitability": {
                    "deal_amount": 6000,
                    "estimated_cost": 5000,
                    "expected_margin": 0.167,
                    "margin_assessment": "목표 마진(20%) 미달",
                },
                "team_composition": [
                    {"role": "PM", "count": 1, "duration_months": 3},
                ],
                "work_breakdown": [
                    {
                        "area": "데이터 파이프라인",
                        "is_reusable": True,
                        "reuse_ratio": 0.6,
                        "effort_person_months": 1.2,
                        "description": "기존 파이프라인 모듈 재활용",
                    },
                ],
            },
            risks=[
                {
                    "category": "기술 리스크",
                    "item": "신규 기술",
                    "level": "MEDIUM",
                    "description": "LLM 파인튜닝 경험 부족",
                },
            ],
            similar_projects=[
                {
                    "project_name": "유사PJ",
                    "similarity_score": 0.85,
                    "lessons_learned": "일정 관리 중요",
                },
            ],
        )
        assert "75.0" in rendered
        assert "go" in rendered
        assert "기술 적합성" in rendered
        assert "유사PJ" in rendered


class TestRenderPromptShortcut:
    """Test the render_prompt convenience function."""

    def test_render_prompt_returns_tuple(self):
        system, user = render_prompt(
            "deal_structuring",
            system_base="당신은 전문가입니다.",
            deal_input="테스트 딜 정보",
        )
        assert "전문가" in system
        assert "테스트 딜 정보" in user


class TestPromptTemplate:
    """Test PromptTemplate construction."""

    def test_from_dict(self):
        data = {
            "version": "2.0",
            "system_prompt": "Hello {{ name }}",
            "user_prompt": "Analyze {{ deal }}",
            "output_schema": {"type": "object"},
        }
        tpl = PromptTemplate(data=data, name="test")
        assert tpl.version == "2.0"
        assert tpl.output_schema == {"type": "object"}
        assert tpl.render_system(name="World") == "Hello World"
        assert tpl.render_user(deal="deal1") == "Analyze deal1"

    def test_empty_prompts(self):
        data = {}
        tpl = PromptTemplate(data=data, name="empty")
        assert tpl.render_system() == ""
        assert tpl.render_user() == ""


class TestProfileLoading:
    """Test prompt profile loading (full vs compact)."""

    def test_load_prompt_default_profile_is_full(self):
        tpl_full = load_prompt("scoring", profile="full")
        tpl_default = load_prompt("scoring", profile="full")
        assert tpl_full.render_system(system_base="test") == tpl_default.render_system(
            system_base="test",
        )

    def test_load_prompt_compact_profile(self):
        tpl_full = load_prompt("scoring", profile="full")
        tpl_compact = load_prompt("scoring", profile="compact")
        full_system = tpl_full.render_system(system_base="test")
        compact_system = tpl_compact.render_system(system_base="test")
        assert full_system != compact_system
        assert len(compact_system) < len(full_system)

    def test_load_prompt_compact_fallback(self):
        """similar_project has no compact variant — should fall back to full."""
        tpl_full = load_prompt("similar_project", profile="full")
        tpl_compact = load_prompt("similar_project", profile="compact")
        assert tpl_full.render_system(system_base="test") == tpl_compact.render_system(
            system_base="test",
        )

    def test_compact_output_schema_unchanged(self):
        for name in [
            "deal_structuring",
            "scoring",
            "resource_estimation",
            "risk_analysis",
        ]:
            tpl_full = load_prompt(name, profile="full")
            tpl_compact = load_prompt(name, profile="compact")
            assert (
                tpl_full.output_schema == tpl_compact.output_schema
            ), f"{name}: output_schema differs between full and compact"

    def test_compact_prompts_are_shorter(self):
        for name in [
            "system",
            "deal_structuring",
            "scoring",
            "resource_estimation",
            "risk_analysis",
            "final_verdict",
        ]:
            tpl_full = load_prompt(name, profile="full")
            tpl_compact = load_prompt(name, profile="compact")
            full_sys = tpl_full.render_system(
                system_base="base",
                company_context="ctx",
                deal_criteria="criteria",
            )
            compact_sys = tpl_compact.render_system(
                system_base="base",
                company_context="ctx",
                deal_criteria="criteria",
            )
            assert len(compact_sys) < len(
                full_sys,
            ), f"{name}: compact system_prompt is not shorter than full"

    def test_compact_template_from_dict(self):
        data = {
            "system_prompt": "Full system {{ name }}",
            "user_prompt": "Full user {{ deal }}",
            "system_prompt_compact": "Compact system {{ name }}",
            "user_prompt_compact": "Compact user {{ deal }}",
            "output_schema": {"type": "object"},
        }
        tpl = PromptTemplate(data=data, name="test", profile="compact")
        assert tpl.render_system(name="World") == "Compact system World"
        assert tpl.render_user(deal="d1") == "Compact user d1"
        assert tpl.output_schema == {"type": "object"}

    def test_compact_fallback_from_dict(self):
        """When compact keys are missing, fall back to full."""
        data = {
            "system_prompt": "Full system {{ name }}",
            "user_prompt": "Full user {{ deal }}",
        }
        tpl = PromptTemplate(data=data, name="test", profile="compact")
        assert tpl.render_system(name="World") == "Full system World"
        assert tpl.render_user(deal="d1") == "Full user d1"


class TestCompactPromptRendering:
    """Test that compact prompts render correctly with sample data."""

    def test_compact_scoring_renders(self):
        tpl = load_prompt("scoring", profile="compact")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사"},
            scoring_criteria=[
                {"name": "기술 적합성", "weight": 0.2, "description": "기술 스택 매칭"},
            ],
        )
        assert "테스트사" in rendered
        assert "기술 적합성" in rendered

    def test_compact_deal_structuring_renders(self):
        tpl = load_prompt("deal_structuring", profile="compact")
        rendered = tpl.render_user(
            deal_input="삼성전자에서 AI 챗봇 개발을 요청했습니다.",
        )
        assert "삼성전자" in rendered
        assert "customer_name" in rendered

    def test_compact_final_verdict_renders(self):
        tpl = load_prompt("final_verdict", profile="compact")
        rendered = tpl.render_user(
            structured_deal={"customer_name": "테스트사"},
            total_score=75.0,
            verdict="go",
            scores=[
                {
                    "criterion": "기술 적합성",
                    "score": 80,
                    "weight": 0.2,
                    "rationale": "기술 스택 일치",
                },
            ],
            resource_estimate={
                "duration_months": 3,
                "duration_with_buffer": 3.6,
                "cost_breakdown": {
                    "labor_cost": 4000,
                    "overhead_cost": 1000,
                    "total_cost": 5000,
                },
                "profitability": {
                    "deal_amount": 6000,
                    "estimated_cost": 5000,
                    "expected_margin": 0.167,
                    "margin_assessment": "목표 마진(20%) 미달",
                },
                "team_composition": [
                    {"role": "PM", "count": 1, "duration_months": 3},
                ],
                "work_breakdown": [
                    {
                        "area": "데이터 파이프라인",
                        "is_reusable": True,
                        "reuse_ratio": 0.6,
                        "effort_person_months": 1.2,
                        "description": "기존 파이프라인 모듈 재활용",
                    },
                ],
            },
            risks=[
                {
                    "category": "기술 리스크",
                    "item": "신규 기술",
                    "level": "MEDIUM",
                    "description": "LLM 파인튜닝 경험 부족",
                },
            ],
            similar_projects=[],
        )
        assert "75.0" in rendered
        assert "go" in rendered
        assert "기술 적합성" in rendered
