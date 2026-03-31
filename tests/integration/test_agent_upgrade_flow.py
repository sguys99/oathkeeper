"""Integration coverage for Phase 7 agent upgrade flows."""

import asyncio
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.agent.orchestrator.context import get_analysis_context
from backend.app.api.routers import analysis as analysis_router
from backend.app.db.repositories import agent_log_repo, deal_repo
from tests.fixtures.sample_deals import CLEAR_GO_DEAL, HOLD_DEAL

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


SCORES = [
    {"criterion": "기술 적합성", "score": 85, "weight": 0.2, "weighted_score": 17.0},
    {"criterion": "수익성", "score": 80, "weight": 0.2, "weighted_score": 16.0},
    {"criterion": "리소스 가용성", "score": 70, "weight": 0.15, "weighted_score": 10.5},
    {"criterion": "납기 리스크", "score": 68, "weight": 0.15, "weighted_score": 10.2},
    {"criterion": "고객 리스크", "score": 72, "weight": 0.1, "weighted_score": 7.2},
    {"criterion": "요구사항 명확성", "score": 90, "weight": 0.1, "weighted_score": 9.0},
    {"criterion": "전략적 가치", "score": 82, "weight": 0.1, "weighted_score": 8.2},
]


async def _create_log(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    deal_id: uuid.UUID,
    node_name: str,
    step_type: str | None = None,
    parent_log_id: uuid.UUID | None = None,
    step_index: int | None = None,
    worker_name: str | None = None,
    tool_name: str | None = None,
    user_prompt: str | None = None,
    raw_output: str | None = None,
):
    now = datetime.now(UTC)
    async with session_factory() as session:
        log = await agent_log_repo.create(
            session,
            deal_id=deal_id,
            node_name=node_name,
            step_type=step_type,
            parent_log_id=parent_log_id,
            step_index=step_index,
            worker_name=worker_name,
            tool_name=tool_name,
            user_prompt=user_prompt,
            raw_output=raw_output,
            started_at=now,
            completed_at=now,
            duration_ms=15,
        )
        await session.commit()
        return log.id


def _make_fake_graph(
    *,
    deal_id: uuid.UUID,
    session_factory: async_sessionmaker[AsyncSession],
    hold: bool = False,
):
    class FakeGraph:
        async def ainvoke(self, input_dict, config=None):
            ctx = get_analysis_context(str(deal_id))

            if ctx.on_progress:
                await ctx.on_progress("Deal 구조화 중...")
                await asyncio.sleep(0.01)

            root_id = await _create_log(
                session_factory,
                deal_id=deal_id,
                node_name="orchestrator",
                step_type="orchestrator_tool_call",
                raw_output="run_deal_structuring -> run_final_verdict",
            )

            if hold:
                ctx.structured_deal = {
                    "customer_name": None,
                    "missing_fields": [
                        "customer_name",
                        "expected_amount",
                        "duration_months",
                    ],
                }
                ctx.total_score = 0.0
                ctx.verdict = "pending"
                ctx.final_report = "# 분석 보류\n\n필수 정보가 부족합니다."
                return {"messages": []}

            if ctx.on_progress:
                await ctx.on_progress("평가 기준 분석 중...")
                await asyncio.sleep(0.01)

            worker_id = await _create_log(
                session_factory,
                deal_id=deal_id,
                node_name="scoring_worker",
                step_type="worker_start",
                parent_log_id=root_id,
                worker_name="scoring_worker",
                raw_output='{"total_score": 78.1, "verdict": "go"}',
            )
            await _create_log(
                session_factory,
                deal_id=deal_id,
                node_name="scoring_worker:reasoning",
                step_type="reasoning",
                parent_log_id=worker_id,
                worker_name="scoring_worker",
                step_index=0,
                raw_output="Scoring requires weighted criteria calculation.",
            )
            await _create_log(
                session_factory,
                deal_id=deal_id,
                node_name="scoring_worker:tool_call",
                step_type="tool_call",
                parent_log_id=worker_id,
                worker_name="scoring_worker",
                tool_name="calculate_weighted_score",
                step_index=1,
                user_prompt='{"scores": [85, 80, 70, 68, 72, 90, 82]}',
            )
            await _create_log(
                session_factory,
                deal_id=deal_id,
                node_name="scoring_worker:observation",
                step_type="observation",
                parent_log_id=worker_id,
                worker_name="scoring_worker",
                tool_name="calculate_weighted_score",
                step_index=2,
                raw_output='{"total_score": 78.1, "verdict": "go"}',
            )

            if ctx.on_progress:
                await ctx.on_progress("최종 판정 중...")

            ctx.structured_deal = {
                "customer_name": "xx철강",
                "project_overview": "AI 비전 검사 시스템",
                "missing_fields": [],
            }
            ctx.scores = SCORES
            ctx.total_score = 78.1
            ctx.verdict = "go"
            ctx.resource_estimate = {
                "duration_months": 6,
                "team_composition": [{"role": "PM", "count": 1}],
                "profitability": {"expected_margin": 22.5},
            }
            ctx.risks = [
                {
                    "category": "일정",
                    "item": "MES 연동 지연",
                    "probability": "MEDIUM",
                    "impact": "HIGH",
                    "level": "HIGH",
                    "description": "기존 MES 인터페이스 협의 지연 가능성",
                    "mitigation": "초기 인터페이스 워크숍 진행",
                },
            ]
            ctx.similar_projects = [
                {
                    "project_name": "철강 표면 검사 구축",
                    "similarity_score": 0.91,
                    "industry": "제조",
                },
            ]
            ctx.final_report = "# 최종 보고서\n\nGo 권고."
            return {"messages": []}

    return FakeGraph()


class TestAgentUpgradeIntegration:
    async def test_analysis_persists_results_and_tree_logs(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        db_engine,
    ):
        session_factory = async_sessionmaker(
            bind=db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        resp = await integration_client.post("/api/deals/", json=CLEAR_GO_DEAL)
        deal_id = uuid.UUID(resp.json()["id"])

        with patch(
            "backend.app.agent.service.build_graph",
            side_effect=lambda deal_id: _make_fake_graph(
                deal_id=uuid.UUID(deal_id),
                session_factory=session_factory,
            ),
        ):
            trigger_resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")

        assert trigger_resp.status_code == 202

        deal_resp = await integration_client.get(f"/api/deals/{deal_id}")
        assert deal_resp.status_code == 200
        assert deal_resp.json()["status"] == "completed"

        analysis_resp = await integration_client.get(f"/api/deals/{deal_id}/analysis")
        assert analysis_resp.status_code == 200
        analysis = analysis_resp.json()
        assert analysis["verdict"] == "go"
        assert analysis["total_score"] == pytest.approx(78.1)
        assert len(analysis["scores"]) == 7
        assert analysis["resource_estimate"]["duration_months"] == 6

        logs_resp = await integration_client.get(f"/api/deals/{deal_id}/logs", params={"view": "tree"})
        assert logs_resp.status_code == 200
        tree = logs_resp.json()
        assert tree["total_count"] >= 4
        assert len(tree["logs"]) == 1
        root = tree["logs"][0]
        assert root["step_type"] == "orchestrator_tool_call"
        worker = root["children"][0]
        assert worker["step_type"] == "worker_start"
        assert worker["worker_name"] == "scoring_worker"
        assert [child["step_type"] for child in worker["children"]] == [
            "reasoning",
            "tool_call",
            "observation",
        ]

    async def test_hold_analysis_skips_worker_logs(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        db_engine,
    ):
        session_factory = async_sessionmaker(
            bind=db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        resp = await integration_client.post("/api/deals/", json=HOLD_DEAL)
        deal_id = uuid.UUID(resp.json()["id"])

        with patch(
            "backend.app.agent.service.build_graph",
            side_effect=lambda deal_id: _make_fake_graph(
                deal_id=uuid.UUID(deal_id),
                session_factory=session_factory,
                hold=True,
            ),
        ):
            trigger_resp = await integration_client.post(f"/api/deals/{deal_id}/analyze")

        assert trigger_resp.status_code == 202

        analysis_resp = await integration_client.get(f"/api/deals/{deal_id}/analysis")
        analysis = analysis_resp.json()
        assert analysis["verdict"] == "pending"
        assert analysis["total_score"] == 0.0

        logs_resp = await integration_client.get(f"/api/deals/{deal_id}/logs", params={"view": "tree"})
        tree = logs_resp.json()
        assert len(tree["logs"]) == 1
        assert tree["logs"][0]["step_type"] == "orchestrator_tool_call"
        assert tree["logs"][0]["children"] == []

    async def test_status_stream_emits_progress_until_completed(
        self,
        integration_client: AsyncClient,
        patch_analysis_session,
        db_engine,
        monkeypatch,
    ):
        session_factory = async_sessionmaker(
            bind=db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        monkeypatch.setattr(analysis_router, "STATUS_STREAM_POLL_INTERVAL_SECONDS", 0.01)

        resp = await integration_client.post("/api/deals/", json=CLEAR_GO_DEAL)
        deal_id = uuid.UUID(resp.json()["id"])

        async with session_factory() as session:
            deal = await deal_repo.get_by_id(session, deal_id)
            assert deal is not None
            deal.status = "analyzing"
            deal.current_step = "Deal 구조화 중..."
            await session.commit()

        async def update_statuses():
            await asyncio.sleep(0.03)
            async with session_factory() as session:
                deal = await deal_repo.get_by_id(session, deal_id)
                assert deal is not None
                deal.current_step = "평가 기준 분석 중..."
                await session.commit()
            await asyncio.sleep(0.03)
            async with session_factory() as session:
                deal = await deal_repo.get_by_id(session, deal_id)
                assert deal is not None
                deal.status = "completed"
                deal.current_step = None
                await session.commit()

        updater = asyncio.create_task(update_statuses())
        events: list[dict] = []
        try:
            async with integration_client.stream("GET", f"/api/deals/{deal_id}/status") as resp:
                assert resp.status_code == 200
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    events.append(json.loads(line.removeprefix("data: ")))
        finally:
            await updater

        assert [event["status"] for event in events][-1] == "completed"
        assert events[0]["current_step"] == "Deal 구조화 중..."
        assert any(event["current_step"] == "평가 기준 분석 중..." for event in events)
