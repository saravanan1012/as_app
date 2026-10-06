from pathlib import Path

from app.config import get_settings


def vendor_storage_root(vendor_id: int) -> Path:
    """Canonical media root: storage/{vendor_id}/..."""
    root = Path(get_settings().storage_root).resolve()
    path = root / str(vendor_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def vendor_item_storage(vendor_id: int, item_id: int) -> Path:
    path = vendor_storage_root(vendor_id) / "items" / str(item_id)
    path.mkdir(parents=True, exist_ok=True)
    return path
