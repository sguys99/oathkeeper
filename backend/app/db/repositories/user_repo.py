"""User repository — CRUD operations for the users table."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.user import User


async def create(session: AsyncSession, *, email: str, name: str, role: str) -> User:
    user = User(id=uuid.uuid4(), email=email, name=name, role=role)
    session.add(user)
    await session.flush()
    return user


async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await session.get(User, user_id)


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
