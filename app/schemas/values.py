import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.common import NameStr


class ValueCreate(BaseModel):
    name: NameStr
    description: str | None = None


class ValueUpdate(BaseModel):
    name: NameStr | None = None
    description: str | None = None


class ValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
