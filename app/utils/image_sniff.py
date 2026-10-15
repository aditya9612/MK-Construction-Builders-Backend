"""Lightweight image sniffing without Pillow.

Provides extension/MIME/magic-byte checks only. Full decode, dimension
validation, and re-encoding require Pillow (not yet approved).
"""

from __future__ import annotations

from app.schemas.uploaded_media import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    assert_allowed_image_extension,
    assert_allowed_image_mime,
    normalize_extension,
)

# Magic signatures (prefix checks). Not a substitute for image decoding.
_JPEG_MAGIC = (b"\xff\xd8\xff",)
_PNG_MAGIC = (b"\x89PNG\r\n\x1a\n",)
# WebP: RIFF....WEBP
_WEBP_RIFF = b"RIFF"
_WEBP_TAG = b"WEBP"

MIME_BY_EXT = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def sniff_image_mime(header: bytes) -> str | None:
    """Return MIME type from magic bytes, or None if unrecognized."""
    if len(header) < 12:
        return None
    if any(header.startswith(sig) for sig in _JPEG_MAGIC):
        return "image/jpeg"
    if any(header.startswith(sig) for sig in _PNG_MAGIC):
        return "image/png"
    if header.startswith(_WEBP_RIFF) and header[8:12] == _WEBP_TAG:
        return "image/webp"
    return None


def extension_from_mime(mime_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    try:
        return mapping[mime_type.lower().strip()]
    except KeyError as exc:
        raise ValueError(f"Unsupported MIME type '{mime_type}'") from exc


def validate_upload_identity(
    *,
    filename: str | None,
    declared_content_type: str | None,
    header: bytes,
) -> tuple[str, str]:
    """Validate extension, declared MIME, and magic bytes; return (ext, mime).

    Does **not** decode pixels or measure dimensions (Pillow blocker).
    SVG and other formats are rejected.
    """
    if not filename or not filename.strip() or ".." in filename:
        raise ValueError("Invalid upload filename")

    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or name in {".", ".."}:
        raise ValueError("Invalid upload filename")
    if "." not in name:
        raise ValueError("Upload filename must include an extension")
    ext = assert_allowed_image_extension(name.rsplit(".", 1)[-1])


    if ext == "svg" or name.lower().endswith(".svg"):
        raise ValueError("SVG uploads are not allowed")

    sniffed = sniff_image_mime(header)
    if sniffed is None:
        raise ValueError("File content is not a recognized JPEG, PNG, or WebP image")

    sniffed_ext = extension_from_mime(sniffed)
    # jpeg/jpg equivalence
    if normalize_extension(sniffed_ext) != normalize_extension(ext):
        raise ValueError(
            f"File extension '.{ext}' does not match content type '{sniffed}'"
        )

    if declared_content_type:
        declared = declared_content_type.split(";")[0].strip().lower()
        if declared and declared != "application/octet-stream":
            declared = assert_allowed_image_mime(declared)
            if declared != sniffed:
                raise ValueError(
                    f"Declared content type '{declared}' does not match file content '{sniffed}'"
                )

    if sniffed not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError(f"MIME type '{sniffed}' is not allowed")
    if normalize_extension(ext) not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Extension '.{ext}' is not allowed")

    return normalize_extension(ext), sniffed
