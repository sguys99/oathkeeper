"""Settings repository — CRUD for scoring_criteria, company_settings, team_members."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.company_setting import CompanySetting
from backend.app.db.models.scoring_criteria import ScoringCriteria
from backend.app.db.models.team_member import TeamMember

# ---------------------------------------------------------------------------
# ScoringCriteria
# ---------------------------------------------------------------------------


async def list_active_criteria(session: AsyncSession) -> list[ScoringCriteria]:
    result = await session.execute(
        select(ScoringCriteria)
        .where(ScoringCriteria.is_active.is_(True))
        .order_by(ScoringCriteria.display_order),
    )
    return list(result.scalars().all())


async def update_weights(
    session: AsyncSession,
    weights: list[dict],
) -> list[ScoringCriteria]:
    """Update weights for multiple criteria. Each dict needs 'id' and 'weight'."""
    updated = []
    for item in weights:
        criteria = await session.get(ScoringCriteria, item["id"])
        if criteria is not None:
            criteria.weight = item["weight"]
            updated.append(criteria)
    await session.flush()
    return updated


# ---------------------------------------------------------------------------
# CompanySetting
# ---------------------------------------------------------------------------


async def get_setting(session: AsyncSession, key: str) -> CompanySetting | None:
    return await session.get(CompanySetting, key)


async def upsert_setting(
    session: AsyncSession,
    key: str,
    value: str,
    description: str | None = None,
) -> CompanySetting:
    setting = await session.get(CompanySetting, key)
    if setting is None:
        setting = CompanySetting(key=key, value=value, description=description)
        session.add(setting)
    else:
        setting.value = value
        if description is not None:
            setting.description = description
    await session.flush()
    return setting


# ---------------------------------------------------------------------------
# TeamMember
# ---------------------------------------------------------------------------


async def list_team_members(session: AsyncSession) -> list[TeamMember]:
    result = await session.execute(select(TeamMember).order_by(TeamMember.name))
    return list(result.scalars().all())


async def create_team_member(
    session: AsyncSession,
    *,
    name: str,
    role: str,
    monthly_rate: int,
    is_available: bool = True,
    current_project: str | None = None,
    available_from=None,
) -> TeamMember:
    member = TeamMember(
        id=uuid.uuid4(),
        name=name,
        role=role,
        monthly_rate=monthly_rate,
        is_available=is_available,
        current_project=current_project,
        available_from=available_from,
    )
    session.add(member)
    await session.flush()
    return member


async def update_team_member(
    session: AsyncSession,
    member_id: uuid.UUID,
    **kwargs,
) -> TeamMember | None:
    member = await session.get(TeamMember, member_id)
    if member is None:
        return None
    for key, value in kwargs.items():
        setattr(member, key, value)
    await session.flush()
    return member


async def delete_team_member(session: AsyncSession, member_id: uuid.UUID) -> bool:
    result = await session.execute(delete(TeamMember).where(TeamMember.id == member_id))
    await session.flush()
    return result.rowcount > 0
