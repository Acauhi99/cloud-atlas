import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_user_id
from app.schemas.values import ValueCreate, ValueResponse, ValueUpdate
from app.services.values import ValueService

router = APIRouter(prefix="/tags/{tag_id}/values", tags=["values"])


@router.get("", response_model=list[ValueResponse])
async def list_values(
    tag_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[ValueResponse]:
    service = ValueService(session)
    values = await service.list_values(user_id, tag_id)
    return [ValueResponse.model_validate(v) for v in values]


@router.post("", response_model=ValueResponse, status_code=201)
async def create_value(
    tag_id: uuid.UUID,
    data: ValueCreate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> ValueResponse:
    service = ValueService(session)
    value = await service.create_value(user_id, tag_id, data)
    return ValueResponse.model_validate(value)


@router.get("/{value_id}", response_model=ValueResponse)
async def get_value(
    tag_id: uuid.UUID,
    value_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> ValueResponse:
    service = ValueService(session)
    value = await service.get_value(user_id, tag_id, value_id)
    return ValueResponse.model_validate(value)


@router.patch("/{value_id}", response_model=ValueResponse)
async def update_value(
    tag_id: uuid.UUID,
    value_id: uuid.UUID,
    data: ValueUpdate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> ValueResponse:
    if not data.model_fields_set:
        raise HTTPException(status_code=422, detail="Request body must not be empty")

    service = ValueService(session)
    value = await service.update_value(user_id, tag_id, value_id, data)
    return ValueResponse.model_validate(value)


@router.delete("/{value_id}", status_code=204)
async def delete_value(
    tag_id: uuid.UUID,
    value_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ValueService(session)
    await service.delete_value(user_id, tag_id, value_id)
