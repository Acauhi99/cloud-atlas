import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Value
from app.schemas.values import ValueCreate, ValueUpdate


class ValueRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_values(self, tag_id: uuid.UUID) -> list[Value]:
        stmt = (
            select(Value)
            .where(Value.tag_id == tag_id)
            .order_by(Value.created_at, Value.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_value(self, tag_id: uuid.UUID, value_id: uuid.UUID) -> Value | None:
        stmt = select(Value).where(Value.id == value_id, Value.tag_id == tag_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_value(self, tag_id: uuid.UUID, data: ValueCreate) -> Value:
        value = Value(tag_id=tag_id, name=data.name, description=data.description)
        self.session.add(value)
        await self.session.flush()
        return value

    async def update_value(
        self, tag_id: uuid.UUID, value_id: uuid.UUID, data: ValueUpdate
    ) -> Value | None:
        value = await self.get_value(tag_id, value_id)
        if not value:
            return None
        for field, value_ in data.model_dump(exclude_unset=True).items():
            setattr(value, field, value_)
        await self.session.flush()
        return value

    async def delete_value(self, tag_id: uuid.UUID, value_id: uuid.UUID) -> bool:
        value = await self.get_value(tag_id, value_id)
        if not value:
            return False
        await self.session.delete(value)
        await self.session.flush()
        return True
