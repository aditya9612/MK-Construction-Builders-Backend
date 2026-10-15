"""Filesystem media storage for website CMS.

Designed for a durable MEDIA_ROOT (persistent volume). Do not assume
container-ephemeral disk survives redeploys. Deletion always uses an
internal storage_key from the database — never client-supplied paths.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from app.core.media_settings import MediaSettings, get_media_settings
from app.models.cms_enums import MediaFolder


class MediaStorageError(Exception):
    """Raised when storage operations fail safely."""


class MediaStorageService:
    def __init__(self, settings: MediaSettings | None = None):
        self.settings = settings or get_media_settings()

    @property
    def root(self) -> Path:
        return self.settings.media_root

    def ensure_root(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def _validate_folder(self, folder: MediaFolder | str) -> str:
        value = folder.value if isinstance(folder, MediaFolder) else str(folder)
        allowed = {item.value for item in MediaFolder}
        if value not in allowed:
            raise MediaStorageError(f"Folder '{value}' is not allowed")
        if ".." in value or "/" in value or "\\" in value:
            raise MediaStorageError("Invalid media folder")
        return value

    def build_storage_key(self, folder: MediaFolder | str, extension: str) -> tuple[str, str, str]:
        """Return (storage_key, stored_filename, url_path)."""
        folder_name = self._validate_folder(folder)
        ext = extension.lower().lstrip(".")
        if not ext or "/" in ext or "\\" in ext or ".." in ext:
            raise MediaStorageError("Invalid file extension")
        stored_filename = f"{uuid.uuid4().hex}.{ext}"
        storage_key = f"{folder_name}/{stored_filename}"
        url_path = f"{self.settings.url_prefix}/{storage_key}"
        return storage_key, stored_filename, url_path

    def resolve_path(self, storage_key: str) -> Path:
        """Resolve a DB storage_key under MEDIA_ROOT with path-traversal guards."""
        if not storage_key or storage_key.startswith(("/", "\\")) or ".." in storage_key:
            raise MediaStorageError("Invalid storage key")
        parts = storage_key.replace("\\", "/").split("/")
        if len(parts) != 2:
            raise MediaStorageError("Invalid storage key format")
        folder, filename = parts
        self._validate_folder(folder)
        if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
            raise MediaStorageError("Invalid stored filename")

        candidate = (self.root / folder / filename).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise MediaStorageError("Resolved path escapes media root") from exc
        return candidate

    async def save_bytes(self, storage_key: str, data: bytes) -> Path:
        path = self.resolve_path(storage_key)
        await asyncio.to_thread(self._write_bytes, path, data)
        return path

    def _write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise MediaStorageError("Refusing to overwrite existing media file")
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_bytes(data)
            tmp.replace(path)
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)

    async def delete_by_storage_key(self, storage_key: str) -> None:
        path = self.resolve_path(storage_key)
        await asyncio.to_thread(self._unlink_if_exists, path)

    @staticmethod
    def _unlink_if_exists(path: Path) -> None:
        if path.exists() and path.is_file():
            path.unlink()

    def absolute_url(self, url_path: str) -> str:
        if self.settings.public_base_url:
            path = url_path if url_path.startswith("/") else f"/{url_path}"
            return f"{self.settings.public_base_url}{path}"
        return url_path
