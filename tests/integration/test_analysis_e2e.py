"""Integration: Real LLM analysis pipeline end-to-end tests.

These tests call the actual LLM API (no mocking) to verify that the full
analysis pipeline produces valid, well-structured results.  Pinecone is
still mocked because it is a separate service outside this test's scope.

Requires: OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.
Run with:  uv run pytest tests/integration/test_analysis_e2e.py -m integration --timeout=200 -v
"""

import os
import time

import pytest
from httpx import AsyncClient

_has_llm_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.skipif(not _has_llm_key, reason="No LLM API key configured"),
]

# Realistic deal input that gives the LLM enough context to produce a full analysis.
_SAMPLE_DEAL_INPUT = (
    "고객사: xx철강\n"
    "프로젝트명: AI 기반 철강 표면 비전 검사 시스템\n"
    "프로젝트 개요: 열연 코일 생산 라인에 실시간 AI 비전 검사 시스템을 도입하여 "
    "표면 결함(스크래치, 기포, 산화 등)을 자동 탐지하고 분류하는 시스템 구축.\n"
    "기술 요구사항: Python, PyTorch, YOLO v8 기반 객체 탐지, GigE Vision 카메라 연동, "
    "온프레미스 GPU 서버(NVIDIA A100), 실시간 처리(< 100ms/frame), REST API 대시보드.\n"
    "예상 규모: 5억 원\n"
    "기간: 8개월\n"
    "고객 산업: 제조/철강\n"
    "담당자: 김영수 과장\n"
    "특이사항: 기존 MES 시스템과 연동 필요, 24시간 무중단 운영 요구, "
    "1차 PoC 후 본계약 전환 조건.\n"
)


class TestRealLLMAnalysis:
    """End-to-end analysis tests with real LLM calls."""

    async def test_real_llm_full_analysis(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_vector_stores,
        seeded_db,
    ):
        """Happy path: create deal → analyze with real LLM → verify results."""
        # 1. Create deal
        resp = await integration_client.post(
            "/api/deals/",
            json={"title": "E2E 실제 LLM 딜", "raw_input": _SAMPLE_DEAL_INPUT},
        )
        assert resp.status_code == 201
        deal_id = resp.json()["id"]

        # 2. Trigger analysis (runs synchronously via ASGITransport)
        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        # 3. Deal should be completed
        resp = await integration_client.get(f"/api/deals/{deal_id}")
        assert resp.status_code == 200
        deal = resp.json()
        assert deal["status"] == "completed", f"Expected completed, got {deal['status']}"

        # 4. Fetch and validate analysis results
        resp = await integration_client.get(f"/api/deals/{deal_id}/analysis")
        assert resp.status_code == 200
        analysis = resp.json()

        # Verdict
        assert analysis["verdict"] in (
            "go",
            "conditional_go",
            "no_go",
        ), f"Unexpected verdict: {analysis['verdict']}"

        # Total score
        assert analysis["total_score"] is not None
        assert 0 <= analysis["total_score"] <= 100, f"Score out of range: {analysis['total_score']}"

        # Scores — 7 criteria
        assert isinstance(analysis["scores"], list)
        assert len(analysis["scores"]) == 7, f"Expected 7 scores, got {len(analysis['scores'])}"
        for score in analysis["scores"]:
            assert "name" in score
            assert "score" in score
            assert "weight" in score
            assert "reasoning" in score

        # Resource estimate
        assert analysis["resource_estimate"] is not None
        assert isinstance(analysis["resource_estimate"], dict)

        # Risks
        assert isinstance(analysis["risks"], list)
        assert len(analysis["risks"]) > 0, "Expected at least one risk item"
        for risk in analysis["risks"]:
            assert "category" in risk
            assert "severity" in risk

        # Report markdown
        assert analysis["report_markdown"] is not None
        assert len(analysis["report_markdown"]) > 100, "Report markdown seems too short"

    async def test_real_llm_hold_path(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_vector_stores,
        seeded_db,
    ):
        """Minimal input should trigger the hold path (>= 3 missing fields)."""
        resp = await integration_client.post(
            "/api/deals/",
            json={"title": "Hold 경로 딜", "raw_input": "AI 문의"},
        )
        assert resp.status_code == 201
        deal_id = resp.json()["id"]

        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202

        resp = await integration_client.get(f"/api/deals/{deal_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        resp = await integration_client.get(f"/api/deals/{deal_id}/analysis")
        assert resp.status_code == 200
        analysis = resp.json()

        assert (
            analysis["verdict"] == "pending"
        ), f"Expected 'pending' for sparse input, got {analysis['verdict']}"
        assert analysis["total_score"] == 0.0

    async def test_real_llm_response_time(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        mock_vector_stores,
        seeded_db,
    ):
        """Full analysis must complete within 180 seconds (PRD requirement: 3 min)."""
        resp = await integration_client.post(
            "/api/deals/",
            json={"title": "응답시간 테스트 딜", "raw_input": _SAMPLE_DEAL_INPUT},
        )
        deal_id = resp.json()["id"]

        start = time.monotonic()
        resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")
        assert resp.status_code == 202
        elapsed = time.monotonic() - start

        # Verify completion
        resp = await integration_client.get(f"/api/deals/{deal_id}")
        assert resp.json()["status"] == "completed"

        assert elapsed < 180, f"Analysis took {elapsed:.1f}s, exceeding 180s limit"
