"""CMS media upload routes (admin). Not registered until integration approval."""

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.cms_enums import MediaFolder
from app.models.user import User
from app.schemas.common import SuccessResponse
from app.schemas.uploaded_media import UploadedMediaOut
from app.services.upload_service import UploadService

router = APIRouter(prefix="/admin/upload", tags=["CMS Upload"])


@router.post(
    "/image",
    response_model=SuccessResponse[UploadedMediaOut],
    status_code=status.HTTP_201_CREATED,
    summary="Upload a single website image",
)
async def upload_image(
    file: UploadFile = File(...),
    folder: MediaFolder = Form(default=MediaFolder.GALLERY),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await UploadService(db).upload_image(file, folder=folder)
    return SuccessResponse(message="Image uploaded successfully", data=data)


@router.post(
    "/images",
    response_model=SuccessResponse[list[UploadedMediaOut]],
    status_code=status.HTTP_201_CREATED,
    summary="Upload multiple website images",
)
async def upload_images(
    files: list[UploadFile] = File(...),
    folder: MediaFolder = Form(default=MediaFolder.GALLERY),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    data = await UploadService(db).upload_images(files, folder=folder)
    return SuccessResponse(message="Images uploaded successfully", data=data)


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete uploaded media by media ID",
)
async def delete_upload(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete by database media ID only — never by filesystem path."""
    await UploadService(db).delete(file_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
