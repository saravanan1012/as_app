"""Authenticated media uploads (vendor-scoped)."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.core.storage import vendor_item_storage
from app.db import get_db
from app.models import Item, ItemImage

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BYTES = 5 * 1024 * 1024


@router.post("/items/{item_id}/images")
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)

    name = file.filename or "upload.bin"
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        return error("Unsupported image type", status_code=400)

    data = await file.read()
    if len(data) > MAX_BYTES:
        return error("File too large (max 5MB)", status_code=400)

    dest_dir = vendor_item_storage(vendor_id, item_id)
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = dest_dir / fname
    dest.write_bytes(data)
    rel_path = f"{vendor_id}/items/{item_id}/{fname}"

    if is_primary:
        for img in db.scalars(
            select(ItemImage).where(ItemImage.item_id == item_id, ItemImage.vendor_id == vendor_id)
        ).all():
            img.is_primary = False
        item.primary_image = rel_path

    img = ItemImage(
        vendor_id=vendor_id,
        item_id=item_id,
        path=rel_path,
        sort_order=0,
        is_primary=is_primary,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return success(
        "Uploaded",
        row(img, ["id", "path", "sort_order", "is_primary"]),
        status_code=201,
    )
