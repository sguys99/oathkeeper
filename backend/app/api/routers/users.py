"""User management endpoints."""

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.exceptions import OathKeeperError
from backend.app.api.schemas.user import UserCreate, UserResponse
from backend.app.db.repositories import user_repo
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await user_repo.create(
        db,
        email=body.email,
        name=body.name,
        role=body.role,
    )
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    x_user_email: str | None = Header(default=None),
) -> UserResponse:
    if x_user_email is None:
        raise OathKeeperError("X-User-Email header is required", status_code=401)
    user = await user_repo.get_by_email(db, x_user_email)
    if user is None:
        raise OathKeeperError(f"User with email {x_user_email} not found", status_code=401)
    return UserResponse.model_validate(user)
