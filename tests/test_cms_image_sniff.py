"""Safe unit tests for CMS image sniffing (no Pillow, no DB)."""

import pytest

from app.utils.image_sniff import sniff_image_mime, validate_upload_identity

JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 20
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
WEBP_HEADER = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 8
SVG_FAKE = b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'></svg>"


def test_sniff_jpeg_png_webp():
    assert sniff_image_mime(JPEG_HEADER) == "image/jpeg"
    assert sniff_image_mime(PNG_HEADER) == "image/png"
    assert sniff_image_mime(WEBP_HEADER) == "image/webp"
    assert sniff_image_mime(SVG_FAKE) is None
    assert sniff_image_mime(b"not-an-image") is None


def test_validate_matching_jpeg():
    ext, mime = validate_upload_identity(
        filename="site.jpg",
        declared_content_type="image/jpeg",
        header=JPEG_HEADER,
    )
    assert ext == "jpg"
    assert mime == "image/jpeg"


def test_reject_extension_mismatch():
    with pytest.raises(ValueError, match="does not match"):
        validate_upload_identity(
            filename="site.png",
            declared_content_type="image/png",
            header=JPEG_HEADER,
        )


def test_reject_svg_extension():
    with pytest.raises(ValueError):
        validate_upload_identity(
            filename="evil.svg",
            declared_content_type="image/svg+xml",
            header=SVG_FAKE,
        )


def test_reject_path_traversal_filename():
    with pytest.raises(ValueError, match="Invalid upload filename"):
        validate_upload_identity(
            filename="../etc/passwd.jpg",
            declared_content_type="image/jpeg",
            header=JPEG_HEADER,
        )


def test_reject_gif():
    gif = b"GIF89a" + b"\x00" * 20
    with pytest.raises(ValueError):
        validate_upload_identity(
            filename="a.gif",
            declared_content_type="image/gif",
            header=gif,
        )
