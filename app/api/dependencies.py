import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def get_user_id(x_user_id: Annotated[str | None, Header()] = None) -> uuid.UUID:
    if not x_user_id:
        raise HTTPException(status_code=422, detail="Header 'X-User-ID' is required")
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="Header 'X-User-ID' must be a valid UUID"
        )


async def get_session() -> AsyncGenerator[AsyncSession]:
    from app.db.session import async_session_factory

    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()
