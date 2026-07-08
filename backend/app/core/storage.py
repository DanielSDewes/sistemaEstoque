"""Local file storage for uploads (product photos)."""
import uuid
from pathlib import Path

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_EXT = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}


def _products_dir() -> Path:
    path = Path(settings.UPLOAD_DIR) / "products"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_product_photo(content: bytes, content_type: str) -> str:
    """Persist a product photo and return its public URL path."""
    ext = _EXT.get(content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    (_products_dir() / filename).write_bytes(content)
    return f"/uploads/products/{filename}"
