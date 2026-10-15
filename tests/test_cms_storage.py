"""Filesystem storage tests using a temporary directory (no DB)."""

import os
from pathlib import Path

import pytest

from app.core.media_settings import clear_media_settings_cache, get_media_settings
from app.models.cms_enums import MediaFolder
from app.services.media_storage import MediaStorageError, MediaStorageService


@pytest.fixture()
def media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "media_volume"
    monkeypatch.setenv("MEDIA_ROOT", str(root))
    monkeypatch.setenv("MEDIA_URL_PREFIX", "/media")
    monkeypatch.delenv("MEDIA_BASE_URL", raising=False)
    clear_media_settings_cache()
    yield root
    clear_media_settings_cache()


@pytest.mark.asyncio
async def test_save_and_resolve_under_root(media_root: Path):
    storage = MediaStorageService(get_media_settings())
    key, filename, url_path = storage.build_storage_key(MediaFolder.PROJECTS, "png")
    assert key.startswith("projects/")
    assert url_path.startswith("/media/projects/")
    path = await storage.save_bytes(key, b"\x89PNG\r\n\x1a\nfake")
    assert path.exists()
    assert media_root in path.parents or path.parent == media_root / "projects"
    assert path == storage.resolve_path(key)


@pytest.mark.asyncio
async def test_refuse_overwrite(media_root: Path):
    storage = MediaStorageService(get_media_settings())
    key, _, _ = storage.build_storage_key(MediaFolder.GALLERY, "jpg")
    await storage.save_bytes(key, b"\xff\xd8\xffone")
    with pytest.raises(MediaStorageError, match="overwrite"):
        await storage.save_bytes(key, b"\xff\xd8\xfftwo")


def test_reject_path_traversal_storage_key(media_root: Path):
    storage = MediaStorageService(get_media_settings())
    with pytest.raises(MediaStorageError):
        storage.resolve_path("../secrets/key.jpg")
    with pytest.raises(MediaStorageError):
        storage.resolve_path("/absolute/path.jpg")
    with pytest.raises(MediaStorageError):
        storage.resolve_path("gallery/../../etc/passwd")


def test_reject_unknown_folder(media_root: Path):
    storage = MediaStorageService(get_media_settings())
    with pytest.raises(MediaStorageError):
        storage.build_storage_key("not-a-folder", "jpg")


@pytest.mark.asyncio
async def test_delete_by_storage_key(media_root: Path):
    storage = MediaStorageService(get_media_settings())
    key, _, _ = storage.build_storage_key(MediaFolder.COMPANY, "webp")
    path = await storage.save_bytes(key, b"RIFFxxxxWEBP")
    assert path.exists()
    await storage.delete_by_storage_key(key)
    assert not path.exists()


def test_settings_do_not_hardcode_domain(media_root: Path):
    settings = get_media_settings()
    assert settings.public_base_url is None
    assert "mkconstruction" not in str(settings.media_root).lower()
