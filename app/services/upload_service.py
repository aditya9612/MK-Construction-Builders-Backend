"""Website CMS image upload service.

Pillow is not approved: width/height are stored as None. Magic-byte and
extension/MIME checks run without decoding image pixels.
"""

from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.core.media_settings import get_media_settings
from app.models.cms_enums import MediaFolder
from app.models.uploaded_media import UploadedMedia
from app.repositories.media_repository import MediaRepository
from app.schemas.uploaded_media import UploadedMediaOut
from app.services.media_storage import MediaStorageError, MediaStorageService
from app.utils.image_sniff import validate_upload_identity


class UploadService:
    def __init__(self, session: AsyncSession, storage: MediaStorageService | None = None):
        self.session = session
        self.repo = MediaRepository(session)
        self.storage = storage or MediaStorageService()
        self.media_settings = get_media_settings()

    async def upload_image(
        self,
        file: UploadFile,
        *,
        folder: MediaFolder = MediaFolder.GALLERY,
    ) -> UploadedMediaOut:
        media = await self._store_one(file, folder=folder)
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            try:
                await self.storage.delete_by_storage_key(media.storage_key)
            except MediaStorageError:
                pass
            raise
        await self.session.refresh(media)
        return UploadedMediaOut.model_validate(media)


    async def upload_images(
        self,
        files: list[UploadFile],
        *,
        folder: MediaFolder = MediaFolder.GALLERY,
    ) -> list[UploadedMediaOut]:
        if not files:
            raise ValidationFailedError("At least one image file is required")
        if len(files) > self.media_settings.max_batch_size:
            raise ValidationFailedError(
                f"Batch limit is {self.media_settings.max_batch_size} files"
            )

        saved: list[UploadedMedia] = []
        stored_keys: list[str] = []
        try:
            for file in files:
                media = await self._store_one(file, folder=folder)
                saved.append(media)
                stored_keys.append(media.storage_key)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            for key in stored_keys:
                try:
                    await self.storage.delete_by_storage_key(key)
                except MediaStorageError:
                    pass
            raise

        for media in saved:
            await self.session.refresh(media)
        return [UploadedMediaOut.model_validate(item) for item in saved]

    async def delete(self, file_id: int) -> None:
        """Delete media by database ID only — never by client filesystem path."""
        media = await self.repo.get(file_id)
        if not media:
            raise NotFoundError("Media file not found")

        refs = await self.repo.count_references(file_id)
        if refs > 0:
            raise ConflictError(
                "Cannot delete media that is referenced by portfolio or gallery content"
            )

        storage_key = media.storage_key
        await self.repo.delete(media)
        await self.session.commit()
        try:
            await self.storage.delete_by_storage_key(storage_key)
        except MediaStorageError:
            # DB row removed; orphan file can be cleaned by ops if unlink fails
            pass

    async def _store_one(self, file: UploadFile, *, folder: MediaFolder) -> UploadedMedia:
        if folder not in MediaFolder:
            raise ValidationFailedError("Invalid media folder")

        raw_name = file.filename or ""
        content_type = file.content_type

        max_bytes = self.media_settings.max_file_size_bytes
        chunk_size = 64 * 1024
        chunks: list[bytes] = []
        total_size = 0

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_bytes:
                raise ValidationFailedError(
                    f"File exceeds maximum size of {max_bytes} bytes"
                )
            chunks.append(chunk)

        if total_size == 0:
            raise ValidationFailedError("Uploaded file is empty")

        data = b"".join(chunks)


        header = data[:64]
        try:
            extension, mime_type = validate_upload_identity(
                filename=raw_name,
                declared_content_type=content_type,
                header=header,
            )
        except ValueError as exc:
            raise ValidationFailedError(str(exc)) from exc

        # Pillow not approved — dimensions intentionally left unset.
        width = None
        height = None

        try:
            storage_key, stored_filename, url_path = self.storage.build_storage_key(
                folder, extension
            )
            self.storage.ensure_root()
            await self.storage.save_bytes(storage_key, data)
        except MediaStorageError as exc:
            raise ValidationFailedError(str(exc)) from exc

        media = UploadedMedia(
            folder=folder.value,
            original_filename=raw_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:255],
            stored_filename=stored_filename,
            storage_key=storage_key,
            url_path=url_path,
            mime_type=mime_type,
            extension=extension,
            size_bytes=len(data),
            width=width,
            height=height,
        )
        try:
            await self.repo.add(media)
        except Exception:
            try:
                await self.storage.delete_by_storage_key(storage_key)
            except MediaStorageError:
                pass
            raise
        return media
