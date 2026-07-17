from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import async_session_factory

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict[str, str]:
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready"}
