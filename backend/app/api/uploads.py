"""Authenticated media uploads (vendor-scoped)."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.core.storage import vendor_item_storage
from app.db import get_db
from app.models import Item, ItemImage
from app.services.item_media import (
    ALLOWED_EXT,
    MAX_IMAGE_BYTES,
    MAX_VIDEO_BYTES,
    VIDEO_EXTS,
    media_kind,
    serialize_media,
    unlink_media_file,
)

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/items/{item_id}/images")
def list_item_images(
    item_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)
    images = db.scalars(
        select(ItemImage)
        .where(ItemImage.item_id == item_id, ItemImage.vendor_id == vendor_id)
        .order_by(ItemImage.sort_order, ItemImage.id)
    ).all()
    return success("Images fetched", {"data": [serialize_media(i) for i in images]})


@router.post("/items/{item_id}/images")
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Query(False),
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
        return error(
            "Unsupported file type (images: jpg/png/webp/gif; video: mp4/webm/mov)",
            status_code=400,
        )

    kind = "video" if ext in VIDEO_EXTS else "image"
    if is_primary and kind == "video":
        return error("Only images can be set as primary", status_code=400)

    data = await file.read()
    max_bytes = MAX_VIDEO_BYTES if kind == "video" else MAX_IMAGE_BYTES
    if len(data) > max_bytes:
        limit_mb = max_bytes // (1024 * 1024)
        return error(f"File too large (max {limit_mb}MB for {kind})", status_code=400)

    dest_dir = vendor_item_storage(vendor_id, item_id)
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = dest_dir / fname
    dest.write_bytes(data)
    rel_path = f"{vendor_id}/items/{item_id}/{fname}"
    media_url = f"/api/media/{rel_path}"

    existing = list(
        db.scalars(
            select(ItemImage).where(ItemImage.item_id == item_id, ItemImage.vendor_id == vendor_id)
        ).all()
    )
    next_order = max((i.sort_order for i in existing), default=-1) + 1

    # First image upload becomes primary when none set
    make_primary = is_primary or (kind == "image" and not item.primary_image)

    if make_primary:
        for img in existing:
            img.is_primary = False
        item.primary_image = media_url

    img = ItemImage(
        vendor_id=vendor_id,
        item_id=item_id,
        path=media_url,
        sort_order=next_order,
        is_primary=make_primary,
    )
    db.add(img)
    db.commit()
    db.refresh(img)
    return success("Uploaded", serialize_media(img), status_code=201)


@router.patch("/items/{item_id}/images/{image_id}")
def patch_item_image(
    item_id: int,
    image_id: int,
    is_primary: bool = Query(True),
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)
    img = db.get(ItemImage, image_id)
    if not img or img.item_id != item_id or img.vendor_id != vendor_id:
        return error("Image not found", status_code=404)
    if media_kind(img.path or "") == "video":
        return error("Only images can be set as primary", status_code=400)

    if is_primary:
        for other in db.scalars(
            select(ItemImage).where(ItemImage.item_id == item_id, ItemImage.vendor_id == vendor_id)
        ).all():
            other.is_primary = False
        img.is_primary = True
        item.primary_image = img.path
    db.commit()
    db.refresh(img)
    return success("Updated", serialize_media(img))


@router.delete("/items/{item_id}/images/{image_id}")
def delete_item_image(
    item_id: int,
    image_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)
    img = db.get(ItemImage, image_id)
    if not img or img.item_id != item_id or img.vendor_id != vendor_id:
        return error("Image not found", status_code=404)

    was_primary = img.is_primary or (item.primary_image == img.path)
    path_url = img.path
    db.delete(img)
    db.flush()

    if was_primary:
        remaining = list(
            db.scalars(
                select(ItemImage)
                .where(ItemImage.item_id == item_id, ItemImage.vendor_id == vendor_id)
                .order_by(ItemImage.sort_order, ItemImage.id)
            ).all()
        )
        next_primary = next((r for r in remaining if media_kind(r.path or "") == "image"), None)
        if next_primary:
            next_primary.is_primary = True
            item.primary_image = next_primary.path
        else:
            item.primary_image = None

    db.commit()
    unlink_media_file(path_url or "")
    return success("Deleted", {"id": image_id})
