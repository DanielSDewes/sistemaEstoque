"""Local file storage for uploads (product photos)."""
import uuid
from pathlib import Path

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def sniff_image_type(content: bytes) -> str | None:
    """Detect the real image type from magic bytes (never trust Content-Type).

    Returns the canonical MIME type, or ``None`` if the bytes are not a
    supported image. This blocks a client from smuggling arbitrary content
    (e.g. HTML/SVG) past a spoofed ``Content-Type`` header.
    """
    if len(content) < 12:
        return None
    if content[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def save_product_photo(content: bytes, content_type: str) -> str:
    """Persist a product photo and return its public URL path."""
    ext = _EXT.get(content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    (_products_dir() / filename).write_bytes(content)
    return f"/uploads/products/{filename}"


def _products_dir() -> Path:
    path = Path(settings.UPLOAD_DIR) / "products"
    path.mkdir(parents=True, exist_ok=True)
    return path
