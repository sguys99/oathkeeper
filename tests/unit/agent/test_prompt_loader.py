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
        assert tpl.version == "1.0"

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
            scoring_criteria=[
                {"name": "기술 적합성", "weight": 20.0, "description": "자사 기술로 구현 가능한가"},
                {"name": "수익성", "weight": 20.0, "description": "목표 마진을 충족하는가"},
            ],
        )
        assert "AI 솔루션 전문 기업" in rendered
        assert "계약 금액 5000만원 이상" in rendered
        assert "기술 적합성" in rendered
        assert "20.0%" in rendered

    def test_system_prompt_without_context(self):
        tpl = load_prompt("system")
        rendered = tpl.render_system()
        assert "컨텍스트가 제공되지 않았습니다" in rendered
        assert "기본 평가 기준" in rendered

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
            company_context="B2B AI 전문 기업",
        )
        assert "customer_name" in rendered
        assert "기술 적합성" in rendered
        assert "B2B AI 전문 기업" in rendered

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
            company_context="보안 중시 기업",
        )
        assert "customer_name" in rendered
        assert "보안 중시 기업" in rendered

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
                "total_cost": 5000,
                "expected_margin": 21.4,
                "team_composition": [{"role": "PM", "count": 1}],
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
