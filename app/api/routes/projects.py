from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_write
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedData, SuccessResponse
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=SuccessResponse[ProjectOut], status_code=status.HTTP_201_CREATED, summary="Create project")
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_write),
):
    return SuccessResponse(message="Project created successfully", data=await ProjectService(db).create(payload))


@router.get("", response_model=SuccessResponse[PaginatedData[ProjectOut]], summary="List projects")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    customer_id: int | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = await ProjectService(db).list(
        page=page,
        page_size=page_size,
        search=search,
        customer_id=customer_id,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SuccessResponse(data=data)


@router.get("/{project_id}", response_model=SuccessResponse[ProjectOut], summary="Get project")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    return SuccessResponse(data=await ProjectService(db).get(project_id))


@router.put("/{project_id}", response_model=SuccessResponse[ProjectOut], summary="Update project")
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_write),
):
    return SuccessResponse(message="Project updated successfully", data=await ProjectService(db).update(project_id, payload))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_write)):
    await ProjectService(db).delete(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
