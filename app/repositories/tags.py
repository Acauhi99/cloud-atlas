import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Tag
from app.schemas.tags import TagCreate, TagUpdate


class TagRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tags(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
    ) -> tuple[list[Tag], int]:
        stmt = select(Tag).where(Tag.user_id == user_id)
        count_stmt = select(func.count()).select_from(Tag).where(Tag.user_id == user_id)
        if name:
            stmt = stmt.where(Tag.name == name)
            count_stmt = count_stmt.where(Tag.name == name)
        stmt = (
            stmt.order_by(Tag.created_at, Tag.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        tags = list(result.scalars().all())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0
        return tags, total

    async def get_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> Tag | None:
        stmt = select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_tag(self, user_id: uuid.UUID, data: TagCreate) -> Tag:
        tag = Tag(user_id=user_id, name=data.name, description=data.description)
        self.session.add(tag)
        await self.session.flush()
        return tag

    async def update_tag(
        self, user_id: uuid.UUID, tag_id: uuid.UUID, data: TagUpdate
    ) -> Tag | None:
        tag = await self.get_tag(user_id, tag_id)
        if not tag:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(tag, field, value)
        await self.session.flush()
        return tag

    async def delete_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> bool:
        tag = await self.get_tag(user_id, tag_id)
        if not tag:
            return False
        await self.session.delete(tag)
        await self.session.flush()
        return True
