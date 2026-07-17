import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.common import NameStr
from app.schemas.values import ValueCreate, ValueResponse


class TagCreate(BaseModel):
    name: NameStr
    description: str | None = None
    values: list[ValueCreate] = []


class TagUpdate(BaseModel):
    name: NameStr | None = None
    description: str | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    values: list[ValueResponse]


class PaginatedTagResponse(BaseModel):
    items: list[TagResponse]
    total: int
    page: int
    page_size: int
    pages: int
