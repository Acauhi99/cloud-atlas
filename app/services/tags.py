import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.repositories.tags import TagRepository
from app.repositories.values import ValueRepository
from app.schemas.tags import TagCreate, TagUpdate


class TagService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tag_repo = TagRepository(session)
        self.value_repo = ValueRepository(session)

    async def list_tags(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        name: str | None = None,
    ) -> tuple[list, int]:
        return await self.tag_repo.list_tags(user_id, page, page_size, name)

    async def get_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID):
        tag = await self.tag_repo.get_tag(user_id, tag_id)
        if not tag:
            raise NotFoundError("Tag not found")
        return tag

    async def create_tag(self, user_id: uuid.UUID, data: TagCreate):
        seen_names: set[str] = set()
        for v in data.values:
            if v.name in seen_names:
                raise ConflictError(f"Duplicate value name '{v.name}' in request")
            seen_names.add(v.name)

        try:
            tag = await self.tag_repo.create_tag(user_id, data)
            for v in data.values:
                await self.value_repo.create_value(tag.id, v)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("A tag with this name already exists")

        await self.session.refresh(tag, ["values"])
        return tag

    async def update_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID, data: TagUpdate):
        try:
            tag = await self.tag_repo.update_tag(user_id, tag_id, data)
            if not tag:
                raise NotFoundError("Tag not found")
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("A tag with this name already exists")
        await self.session.refresh(tag, ["values"])
        return tag

    async def delete_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        deleted = await self.tag_repo.delete_tag(user_id, tag_id)
        if not deleted:
            raise NotFoundError("Tag not found")
        await self.session.commit()
