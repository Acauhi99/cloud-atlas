import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session, get_user_id
from app.schemas.tags import PaginatedTagResponse, TagCreate, TagResponse, TagUpdate
from app.services.tags import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=PaginatedTagResponse)
async def list_tags(
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str | None = Query(None),
) -> PaginatedTagResponse:
    service = TagService(session)
    tags, total = await service.list_tags(user_id, page, page_size, name)
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedTagResponse(
        items=[TagResponse.model_validate(t) for t in tags],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> TagResponse:
    service = TagService(session)
    tag = await service.create_tag(user_id, data)
    return TagResponse.model_validate(tag)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> TagResponse:
    service = TagService(session)
    tag = await service.get_tag(user_id, tag_id)
    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> TagResponse:
    if not data.model_fields_set:
        raise HTTPException(status_code=422, detail="Request body must not be empty")

    service = TagService(session)
    tag = await service.update_tag(user_id, tag_id, data)
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = TagService(session)
    await service.delete_tag(user_id, tag_id)
