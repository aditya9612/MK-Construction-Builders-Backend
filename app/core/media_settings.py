"""Website CMS media configuration via environment variables.

Intentionally separate from ``app.core.config.Settings`` so existing config
files remain untouched until an approved integration phase can merge these
fields. Values are designed for a persistent volume / durable mount —
container-local disk alone is not assumed durable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MediaSettings:
    """Filesystem media settings for website CMS uploads."""

    media_root: Path
    url_prefix: str
    public_base_url: str | None
    max_file_size_bytes: int
    max_batch_size: int


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


@lru_cache
def get_media_settings() -> MediaSettings:
    root = Path(os.getenv("MEDIA_ROOT", "media_storage")).expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    else:
        root = root.resolve()

    prefix = os.getenv("MEDIA_URL_PREFIX", "/media").strip() or "/media"
    if not prefix.startswith("/"):
        prefix = f"/{prefix}"
    prefix = prefix.rstrip("/") or "/media"

    base = os.getenv("MEDIA_BASE_URL", "").strip() or None
    if base:
        base = base.rstrip("/")

    return MediaSettings(
        media_root=root,
        url_prefix=prefix,
        public_base_url=base,
        max_file_size_bytes=_env_int("MEDIA_MAX_FILE_SIZE_BYTES", 5 * 1024 * 1024),
        max_batch_size=_env_int("MEDIA_MAX_BATCH_SIZE", 20),
    )


def clear_media_settings_cache() -> None:
    """Test helper to reload env-driven settings."""
    get_media_settings.cache_clear()
