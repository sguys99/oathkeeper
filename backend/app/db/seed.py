"""Seed database with default scoring criteria, company settings, and team members."""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.defaults_loader import load_defaults
from backend.app.db.models.company_setting import CompanySetting
from backend.app.db.models.cost_item import CostItem
from backend.app.db.models.scoring_criteria import ScoringCriteria
from backend.app.db.models.team_member import TeamMember
from backend.app.db.session import AsyncSessionLocal

SCORING_CRITERIA_DEFAULTS = load_defaults("scoring_criteria")
COMPANY_SETTINGS_DEFAULTS = load_defaults("company_settings")
TEAM_MEMBER_DEFAULTS = load_defaults("team_members")
COST_ITEM_DEFAULTS = load_defaults("cost_items")


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
    """Upsert default company settings from YAML. Returns count of new inserts."""
    count = 0
    for item in COMPANY_SETTINGS_DEFAULTS:
        existing = await session.get(CompanySetting, item["key"])
        if existing is None:
            session.add(CompanySetting(**item))
            count += 1
        else:
            existing.value = item["value"]
            if "description" in item:
                existing.description = item["description"]
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
