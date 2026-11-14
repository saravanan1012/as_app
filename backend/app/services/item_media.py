"""Item image/video helpers (extension-based media type)."""

from pathlib import Path

from app.api.serialize import row
from app.models import ItemImage

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTS = {".mp4", ".webm", ".mov"}
ALLOWED_EXT = IMAGE_EXTS | VIDEO_EXTS
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024
IMAGE_FIELDS = ["id", "path", "sort_order", "is_primary"]


def media_kind(path: str) -> str:
    ext = Path(path.split("?")[0]).suffix.lower()
    return "video" if ext in VIDEO_EXTS else "image"


def serialize_media(img: ItemImage) -> dict:
    data = row(img, IMAGE_FIELDS)
    data["media_type"] = media_kind(img.path or "")
    return data


def unlink_media_file(path_url: str) -> None:
    """Best-effort delete of /api/media/{rel} under storage root."""
    if not path_url or not path_url.startswith("/api/media/"):
        return
    from app.config import get_settings

    rel = path_url[len("/api/media/") :].lstrip("/")
    full = Path(get_settings().storage_root).resolve() / rel
    try:
        if full.is_file():
            full.unlink()
    except OSError:
        pass
