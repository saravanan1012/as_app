"""Stock balance + stock_movements ledger (FOR UPDATE)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item, Location, Stock, StockMovement

MOVEMENT_REASONS = frozenset(
    {
        "PO_RECEIVE",
        "PO_RETURN",
        "SO_SALE",
        "SO_RETURN",
        "SO_CANCEL",
        "ADJUSTMENT",
        "TRANSFER_IN",
        "TRANSFER_OUT",
    }
)


class StockError(Exception):
    pass


def _get_or_create_stock(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    for_update: bool = True,
) -> Stock:
    q = select(Stock).where(
        Stock.vendor_id == vendor_id,
        Stock.item_id == item_id,
        Stock.location_id == location_id,
    )
    if for_update:
        q = q.with_for_update()
    row = db.scalar(q)
    if row:
        return row
    # Validate FKs belong to vendor before insert
    item = db.get(Item, item_id)
    loc = db.get(Location, location_id)
    if not item or item.vendor_id != vendor_id:
        raise StockError(f"Item {item_id} not found")
    if not loc or loc.vendor_id != vendor_id:
        raise StockError(f"Location {location_id} not found")
    row = Stock(
        vendor_id=vendor_id,
        item_id=item_id,
        location_id=location_id,
        quantity_on_hand=0,
    )
    db.add(row)
    db.flush()
    if for_update:
        row = db.scalar(
            select(Stock)
            .where(Stock.id == row.id)
            .with_for_update()
        )
        assert row is not None
    return row


def apply_delta(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    qty_delta: int,
    reason: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: str | None = None,
    allow_negative: bool = False,
) -> Stock:
    if reason not in MOVEMENT_REASONS:
        raise StockError(f"Invalid movement reason: {reason}")
    if qty_delta == 0:
        raise StockError("qty_delta cannot be zero")

    stock = _get_or_create_stock(
        db, vendor_id=vendor_id, item_id=item_id, location_id=location_id, for_update=True
    )
    new_qty = int(stock.quantity_on_hand) + int(qty_delta)
    if new_qty < 0 and not allow_negative:
        item = db.get(Item, item_id)
        name = item.name if item else f"Item {item_id}"
        raise StockError(
            f"Insufficient stock for {name} (need {abs(qty_delta)}, have {stock.quantity_on_hand})"
        )
    stock.quantity_on_hand = new_qty
    db.add(
        StockMovement(
            vendor_id=vendor_id,
            item_id=item_id,
            location_id=location_id,
            qty_delta=qty_delta,
            qty_after=new_qty,
            reason=reason,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by,
        )
    )
    db.flush()
    return stock


def add_stock(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    quantity: int,
    reason: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: str | None = None,
) -> Stock:
    if quantity <= 0:
        raise StockError("quantity must be positive")
    return apply_delta(
        db,
        vendor_id=vendor_id,
        item_id=item_id,
        location_id=location_id,
        qty_delta=quantity,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )


def deduct_stock(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    quantity: int,
    reason: str,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: str | None = None,
) -> Stock:
    if quantity <= 0:
        raise StockError("quantity must be positive")
    return apply_delta(
        db,
        vendor_id=vendor_id,
        item_id=item_id,
        location_id=location_id,
        qty_delta=-quantity,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )


def reserve_stock(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    quantity: int,
) -> Stock:
    """Hold qty for unpaid Razorpay orders (does not write movements)."""
    if quantity <= 0:
        raise StockError("quantity must be positive")
    stock = _get_or_create_stock(
        db, vendor_id=vendor_id, item_id=item_id, location_id=location_id, for_update=True
    )
    available = int(stock.quantity_on_hand) - int(stock.quantity_reserved)
    if available < quantity:
        item = db.get(Item, item_id)
        name = item.name if item else f"Item {item_id}"
        raise StockError(f"Insufficient stock for {name} (need {quantity}, available {available})")
    stock.quantity_reserved = int(stock.quantity_reserved) + quantity
    db.flush()
    return stock


def release_reservation(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    quantity: int,
) -> Stock:
    if quantity <= 0:
        raise StockError("quantity must be positive")
    stock = _get_or_create_stock(
        db, vendor_id=vendor_id, item_id=item_id, location_id=location_id, for_update=True
    )
    stock.quantity_reserved = max(0, int(stock.quantity_reserved) - quantity)
    db.flush()
    return stock


def consume_reservation(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    location_id: int,
    quantity: int,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: str | None = None,
) -> Stock:
    """Convert reserved qty into a sale (on_hand ↓, reserved ↓, SO_SALE movement)."""
    if quantity <= 0:
        raise StockError("quantity must be positive")
    stock = _get_or_create_stock(
        db, vendor_id=vendor_id, item_id=item_id, location_id=location_id, for_update=True
    )
    if int(stock.quantity_reserved) < quantity:
        raise StockError("Reservation shortfall")
    if int(stock.quantity_on_hand) < quantity:
        item = db.get(Item, item_id)
        name = item.name if item else f"Item {item_id}"
        raise StockError(f"Insufficient stock for {name}")
    stock.quantity_reserved = int(stock.quantity_reserved) - quantity
    stock.quantity_on_hand = int(stock.quantity_on_hand) - quantity
    db.add(
        StockMovement(
            vendor_id=vendor_id,
            item_id=item_id,
            location_id=location_id,
            qty_delta=-quantity,
            qty_after=int(stock.quantity_on_hand),
            reason="SO_SALE",
            reference_type=reference_type,
            reference_id=reference_id,
            created_by=created_by,
        )
    )
    db.flush()
    return stock
