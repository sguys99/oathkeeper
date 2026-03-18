"""Seed database with default scoring criteria, company settings, and team members."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.company_setting import CompanySetting
from backend.app.db.models.cost_item import CostItem
from backend.app.db.models.scoring_criteria import ScoringCriteria
from backend.app.db.models.team_member import TeamMember
from backend.app.db.session import AsyncSessionLocal

SCORING_CRITERIA_DEFAULTS = [
    {
        "name": "기술 적합성",
        "weight": 0.200,
        "description": "현재 기술 스택으로 구현 가능한가? 학습 곡선은?",
        "display_order": 1,
    },
    {
        "name": "수익성",
        "weight": 0.200,
        "description": "예상 매출 대비 비용이 적절한가? 마진 목표를 충족하는가?",
        "display_order": 2,
    },
    {
        "name": "리소스 가용성",
        "weight": 0.150,
        "description": "가용 인력/장비가 있는가? 다른 프로젝트와 충돌하지 않는가?",
        "display_order": 3,
    },
    {
        "name": "납기 리스크",
        "weight": 0.150,
        "description": "고객 요구 납기가 현실적인가? 충분한 버퍼가 있는가?",
        "display_order": 4,
    },
    {
        "name": "요구사항 명확성",
        "weight": 0.100,
        "description": "요구사항이 구체적인가? 스코프 크리프 위험은?",
        "display_order": 5,
    },
    {
        "name": "전략적 가치",
        "weight": 0.100,
        "description": "레퍼런스 케이스, 신규 시장 진출, 기술 축적 등 장기적 가치",
        "display_order": 6,
    },
    {
        "name": "고객 리스크",
        "weight": 0.100,
        "description": "고객 지불 능력, 의사결정 구조, 과거 협업 이력",
        "display_order": 7,
    },
]

COMPANY_SETTINGS_DEFAULTS = [
    {
        "key": "business_direction",
        "value": "AI/ML 기반 B2B 솔루션 개발",
        "description": "사업 방향 및 범위",
    },
    {
        "key": "deal_criteria",
        "value": '{"min_margin_rate": 20, "preferred_industries": ["금융", "제조", "유통"]}',
        "description": "딜 평가 기본 기준 (JSON)",
    },
    {
        "key": "short_term_strategy",
        "value": "기존 고객 확대 및 레퍼런스 확보",
        "description": "단기 전략 방향",
    },
    {
        "key": "minimum_margin_rate",
        "value": "20",
        "description": "최소 허용 마진율 (%)",
    },
]


TEAM_MEMBER_DEFAULTS = [
    {"name": "김BE", "role": "BE", "monthly_rate": 1500},
    {"name": "이BE", "role": "BE", "monthly_rate": 2000},
    {"name": "김dev", "role": "DevOps", "monthly_rate": 1000},
    {"name": "이dev", "role": "DevOps", "monthly_rate": 1500},
    {"name": "김FE", "role": "FE", "monthly_rate": 1500},
    {"name": "이FE", "role": "FE", "monthly_rate": 1000},
    {"name": "김ML", "role": "MLE", "monthly_rate": 2000},
    {"name": "이ML", "role": "MLE", "monthly_rate": 1500},
    {"name": "김PM", "role": "PM", "monthly_rate": 2000},
    {"name": "이PM", "role": "PM", "monthly_rate": 1000},
]

COST_ITEM_DEFAULTS = [
    {"name": "HW 서버 비용", "amount": 0, "description": "하드웨어 서버 구매/임대 비용"},
    {"name": "SW 라이선스 비용", "amount": 0, "description": "소프트웨어 라이선스 비용"},
    {"name": "클라우드 인프라 비용", "amount": 0, "description": "클라우드 인프라 사용 비용"},
    {"name": "기타 비용", "amount": 0, "description": "기타 프로젝트 관련 비용"},
]


async def seed_scoring_criteria(session: AsyncSession) -> int:
    """Insert default scoring criteria if table is empty. Returns count."""
    result = await session.execute(select(ScoringCriteria.id).limit(1))
    if result.scalar_one_or_none() is not None:
        return 0

    count = 0
    for item in SCORING_CRITERIA_DEFAULTS:
        criteria = ScoringCriteria(id=uuid.uuid4(), **item)
        session.add(criteria)
        count += 1
    return count


async def seed_company_settings(session: AsyncSession) -> int:
    """Insert default company settings if table is empty. Returns count."""
    result = await session.execute(select(CompanySetting.key).limit(1))
    if result.scalar_one_or_none() is not None:
        return 0

    count = 0
    for item in COMPANY_SETTINGS_DEFAULTS:
        setting = CompanySetting(**item)
        session.add(setting)
        count += 1
    return count


async def seed_team_members(session: AsyncSession) -> int:
    """Insert default team members if table is empty. Returns count."""
    result = await session.execute(select(TeamMember.id).limit(1))
    if result.scalar_one_or_none() is not None:
        return 0

    count = 0
    for item in TEAM_MEMBER_DEFAULTS:
        member = TeamMember(id=uuid.uuid4(), **item)
        session.add(member)
        count += 1
    return count


async def seed_cost_items(session: AsyncSession) -> int:
    """Insert default cost items if table is empty. Returns count."""
    result = await session.execute(select(CostItem.id).limit(1))
    if result.scalar_one_or_none() is not None:
        return 0

    count = 0
    for item in COST_ITEM_DEFAULTS:
        cost_item = CostItem(id=uuid.uuid4(), **item)
        session.add(cost_item)
        count += 1
    return count


async def run_seed() -> None:
    """Run all seed functions."""
    async with AsyncSessionLocal() as session:
        criteria_count = await seed_scoring_criteria(session)
        settings_count = await seed_company_settings(session)
        members_count = await seed_team_members(session)
        cost_items_count = await seed_cost_items(session)
        await session.commit()

    print(
        f"Seeded {criteria_count} scoring criteria, "
        f"{settings_count} company settings, "
        f"{members_count} team members, "
        f"{cost_items_count} cost items.",
    )


if __name__ == "__main__":
    asyncio.run(run_seed())
