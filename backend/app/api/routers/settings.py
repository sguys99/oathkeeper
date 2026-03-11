"""Admin settings endpoints — scoring criteria, company settings, team members."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import OathKeeperError
from backend.app.api.schemas.settings import (
    CompanySettingResponse,
    CompanySettingUpsert,
    ScoringCriteriaResponse,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    WeightUpdateRequest,
)
from backend.app.db.repositories import settings_repo
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])


# ---------------------------------------------------------------------------
# Scoring Criteria
# ---------------------------------------------------------------------------


@router.get("/criteria", response_model=list[ScoringCriteriaResponse])
async def list_criteria(
    db: AsyncSession = Depends(get_db),
) -> list[ScoringCriteriaResponse]:
    items = await settings_repo.list_active_criteria(db)
    return [ScoringCriteriaResponse.model_validate(c) for c in items]


@router.put("/criteria/weights", response_model=list[ScoringCriteriaResponse])
async def update_weights(
    body: WeightUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> list[ScoringCriteriaResponse]:
    weights = [{"id": w.id, "weight": w.weight} for w in body.weights]
    updated = await settings_repo.update_weights(db, weights)
    for c in updated:
        await db.refresh(c)
    return [ScoringCriteriaResponse.model_validate(c) for c in updated]


# ---------------------------------------------------------------------------
# Company Settings
# ---------------------------------------------------------------------------


@router.get("/company/{key}", response_model=CompanySettingResponse)
async def get_company_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
) -> CompanySettingResponse:
    setting = await settings_repo.get_setting(db, key)
    if setting is None:
        raise OathKeeperError(f"Setting '{key}' not found", status_code=404)
    return CompanySettingResponse.model_validate(setting)


@router.put("/company", response_model=CompanySettingResponse)
async def upsert_company_setting(
    body: CompanySettingUpsert,
    db: AsyncSession = Depends(get_db),
) -> CompanySettingResponse:
    setting = await settings_repo.upsert_setting(
        db,
        key=body.key,
        value=body.value,
        description=body.description,
    )
    await db.refresh(setting)
    return CompanySettingResponse.model_validate(setting)


# ---------------------------------------------------------------------------
# Team Members
# ---------------------------------------------------------------------------


@router.get("/team-members", response_model=list[TeamMemberResponse])
async def list_team_members(
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    items = await settings_repo.list_team_members(db)
    return [TeamMemberResponse.model_validate(m) for m in items]


@router.post(
    "/team-members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_team_member(
    body: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    member = await settings_repo.create_team_member(
        db,
        name=body.name,
        role=body.role,
        monthly_rate=body.monthly_rate,
        is_available=body.is_available,
        current_project=body.current_project,
        available_from=body.available_from,
    )
    return TeamMemberResponse.model_validate(member)


@router.put("/team-members/{member_id}", response_model=TeamMemberResponse)
async def update_team_member(
    member_id: uuid.UUID,
    body: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise OathKeeperError("No fields to update", status_code=400)
    member = await settings_repo.update_team_member(db, member_id, **update_data)
    if member is None:
        raise OathKeeperError(f"Team member {member_id} not found", status_code=404)
    await db.refresh(member)
    return TeamMemberResponse.model_validate(member)


@router.delete("/team-members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted = await settings_repo.delete_team_member(db, member_id)
    if not deleted:
        raise OathKeeperError(f"Team member {member_id} not found", status_code=404)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
