from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer

PARTY_TYPES = {"DISTRIBUTOR", "DEALER", "RETAILER", "CUSTOMER"}
TRADE_PARTY_TYPES = {"DISTRIBUTOR", "DEALER", "RETAILER"}
ACQUISITION_SOURCES = {"ONLINE", "FB_LEAD", "WALK_IN", "PHONE", "REFERRAL", "OTHER"}

# child_type -> allowed parent party_types (None means parent_id must be null)
ALLOWED_PARENTS: dict[str, set[str | None]] = {
    "DISTRIBUTOR": {None},
    "DEALER": {None, "DISTRIBUTOR"},
    "RETAILER": {None, "DEALER", "DISTRIBUTOR"},
    "CUSTOMER": {None, "RETAILER", "DEALER", "DISTRIBUTOR"},
}

ROLE_TO_PARTY = {
    "DISTRIBUTOR": "DISTRIBUTOR",
    "DEALER": "DEALER",
    "RETAILER": "RETAILER",
    "CUSTOMER": "CUSTOMER",
}


def validate_party_link(
    db: Session,
    *,
    vendor_id: int,
    party_type: str,
    parent_id: int | None,
    self_id: int | None = None,
) -> None:
    pt = (party_type or "CUSTOMER").upper()
    if pt not in PARTY_TYPES:
        raise ValueError(f"Invalid party_type: {party_type}")

    allowed = ALLOWED_PARENTS[pt]
    if parent_id is None:
        if None not in allowed:
            raise ValueError(f"{pt} requires a parent")
        return

    if None in allowed and len(allowed) == 1:
        # only null allowed (DISTRIBUTOR)
        raise ValueError(f"{pt} cannot have a parent")

    parent = db.get(Customer, parent_id)
    if not parent or parent.vendor_id != vendor_id:
        raise ValueError("Parent not found in this vendor")
    if parent.party_type == "CUSTOMER":
        raise ValueError("CUSTOMER cannot be a parent")
    if parent.party_type not in {p for p in allowed if p}:
        raise ValueError(f"{pt} parent must be one of {sorted(p for p in allowed if p)}")
    if self_id and parent_id == self_id:
        raise ValueError("Cannot parent to self")

    # cycle check: walk up from parent
    seen = {self_id} if self_id else set()
    cursor = parent
    while cursor:
        if cursor.id in seen:
            raise ValueError("Hierarchy cycle detected")
        seen.add(cursor.id)
        if not cursor.parent_id:
            break
        cursor = db.get(Customer, cursor.parent_id)


def validate_acquisition_source(source: str | None) -> str | None:
    if source is None or source == "":
        return None
    s = source.upper()
    if s not in ACQUISITION_SOURCES:
        raise ValueError(f"Invalid acquisition_source: {source}")
    return s


def list_children(db: Session, vendor_id: int, parent_id: int) -> list[Customer]:
    return list(
        db.scalars(
            select(Customer).where(
                Customer.vendor_id == vendor_id,
                Customer.parent_id == parent_id,
            )
        ).all()
    )


def get_party_for_user(db: Session, vendor_id: int, user_id: int) -> Customer | None:
    return db.scalar(
        select(Customer).where(Customer.vendor_id == vendor_id, Customer.user_id == user_id)
    )


def list_descendant_ids(db: Session, vendor_id: int, root_id: int) -> set[int]:
    """BFS all descendants under root (not including root)."""
    found: set[int] = set()
    frontier = [root_id]
    while frontier:
        parent_id = frontier.pop()
        children = list_children(db, vendor_id, parent_id)
        for ch in children:
            if ch.id in found:
                continue
            found.add(ch.id)
            frontier.append(ch.id)
    return found


def assert_in_downline(
    db: Session,
    *,
    vendor_id: int,
    actor_party: Customer,
    target_id: int,
    include_self: bool = True,
) -> Customer:
    target = db.get(Customer, target_id)
    if not target or target.vendor_id != vendor_id:
        raise ValueError("Party not found")
    if include_self and target.id == actor_party.id:
        return target
    descendants = list_descendant_ids(db, vendor_id, actor_party.id)
    if target.id not in descendants:
        raise ValueError("Party is not in your downline")
    return target


def can_order_for(actor_party: Customer, target: Customer) -> bool:
    """Whether actor may create an order billing target (self or descendant)."""
    if actor_party.id == target.id:
        return True
    # CUSTOMER never orders for others
    if actor_party.party_type == "CUSTOMER":
        return False
    return True  # caller must verify downline membership


def order_scope_party_ids(db: Session, vendor_id: int, actor_party: Customer) -> set[int]:
    """Party ids whose orders the actor may view (self + descendants)."""
    ids = {actor_party.id}
    ids |= list_descendant_ids(db, vendor_id, actor_party.id)
    return ids
