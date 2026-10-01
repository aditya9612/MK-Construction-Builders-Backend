from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_masters
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.term import TermCreate, TermOut, TermUpdate
from app.services.term_service import TermService

router = APIRouter(prefix="/terms", tags=["Terms"])


@router.post("", response_model=SuccessResponse[TermOut], status_code=status.HTTP_201_CREATED, summary="Create term")
async def create_term(payload: TermCreate, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    return SuccessResponse(message="Term created successfully", data=await TermService(db).create(payload))


@router.get("", response_model=SuccessResponse[PaginatedData[TermOut]], summary="List terms")
async def list_terms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return SuccessResponse(data=await TermService(db).list(page=page, page_size=page_size, search=search, is_active=is_active))


@router.get("/{term_id}", response_model=SuccessResponse[TermOut], summary="Get term")
async def get_term(term_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await TermService(db).get(term_id))


@router.put("/{term_id}", response_model=SuccessResponse[TermOut], summary="Update term")
async def update_term(term_id: int, payload: TermUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    return SuccessResponse(message="Term updated successfully", data=await TermService(db).update(term_id, payload))


@router.delete("/{term_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate term")
async def delete_term(term_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_masters)):
    await TermService(db).delete(term_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
