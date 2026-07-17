import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.repositories.tags import TagRepository
from app.repositories.values import ValueRepository
from app.schemas.values import ValueCreate, ValueUpdate


class ValueService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tag_repo = TagRepository(session)
        self.value_repo = ValueRepository(session)

    async def _ensure_tag(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> None:
        tag = await self.tag_repo.get_tag(user_id, tag_id)
        if not tag:
            raise NotFoundError("Tag not found")

    async def list_values(self, user_id: uuid.UUID, tag_id: uuid.UUID) -> list:
        await self._ensure_tag(user_id, tag_id)
        return await self.value_repo.list_values(tag_id)

    async def get_value(
        self, user_id: uuid.UUID, tag_id: uuid.UUID, value_id: uuid.UUID
    ):
        await self._ensure_tag(user_id, tag_id)
        value = await self.value_repo.get_value(tag_id, value_id)
        if not value:
            raise NotFoundError("Value not found")
        return value

    async def create_value(
        self, user_id: uuid.UUID, tag_id: uuid.UUID, data: ValueCreate
    ):
        await self._ensure_tag(user_id, tag_id)
        try:
            value = await self.value_repo.create_value(tag_id, data)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("A value with this name already exists in this tag")
        await self.session.refresh(value)
        return value

    async def update_value(
        self,
        user_id: uuid.UUID,
        tag_id: uuid.UUID,
        value_id: uuid.UUID,
        data: ValueUpdate,
    ):
        await self._ensure_tag(user_id, tag_id)
        try:
            value = await self.value_repo.update_value(tag_id, value_id, data)
            if not value:
                raise NotFoundError("Value not found")
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError("A value with this name already exists in this tag")
        await self.session.refresh(value)
        return value

    async def delete_value(
        self, user_id: uuid.UUID, tag_id: uuid.UUID, value_id: uuid.UUID
    ) -> None:
        await self._ensure_tag(user_id, tag_id)
        deleted = await self.value_repo.delete_value(tag_id, value_id)
        if not deleted:
            raise NotFoundError("Value not found")
        await self.session.commit()
