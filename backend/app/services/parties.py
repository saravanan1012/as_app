from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Customer, User

PARTY_TYPES = {"DISTRIBUTOR", "DEALER", "RETAILER", "CUSTOMER"}
TRADE_PARTY_TYPES = {"DISTRIBUTOR", "DEALER", "RETAILER"}
PORTAL_ROLES = PARTY_TYPES  # login role matches party_type
STAFF_ROLES = {"SUPER_ADMIN", "ADMIN", "MANAGER", "STAFF"}
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


def allowed_child_types(party_type: str) -> list[str]:
    """Party types that may hang directly under this parent."""
    pt = (party_type or "").upper()
    return sorted(
        child
        for child, parents in ALLOWED_PARENTS.items()
        if pt in {p for p in parents if p}
    )


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


def create_or_link_portal_login(
    db: Session,
    *,
    vendor_id: int,
    party: Customer,
    email: str,
    password: str,
    name: str | None = None,
    phone: str | None = None,
) -> User:
    """Create (or reuse) a portal User and attach it to party via user_id."""
    if party.user_id:
        raise ValueError("Party already has a portal login")

    email_norm = email.strip().lower()
    if not email_norm:
        raise ValueError("Email is required")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    role = (party.party_type or "CUSTOMER").upper()
    if role not in PORTAL_ROLES:
        raise ValueError(f"Cannot provision portal login for party_type {role}")

    existing = db.scalar(select(User).where(User.email == email_norm))
    if existing:
        if existing.vendor_id not in (None, vendor_id):
            raise ValueError("Email already exists for another vendor")
        if existing.role in STAFF_ROLES or existing.role == "SUPER_ADMIN":
            raise ValueError("Email belongs to a staff account")
        linked = db.scalar(
            select(Customer).where(
                Customer.vendor_id == vendor_id,
                Customer.user_id == existing.id,
            )
        )
        if linked:
            raise ValueError("Email is already linked to another party")
        if existing.role not in PORTAL_ROLES:
            raise ValueError("Email belongs to an incompatible account")
        existing.role = role
        existing.status = "ACTIVE"
        existing.vendor_id = vendor_id
        if name:
            existing.name = name.strip()
        if phone and not existing.phone:
            existing.phone = phone
        existing.password = hash_password(password)
        user = existing
    else:
        user = User(
            email=email_norm,
            name=(name or party.name).strip(),
            role=role,
            status="ACTIVE",
            vendor_id=vendor_id,
            phone=phone or party.phone,
            password=hash_password(password),
        )
        db.add(user)
        db.flush()

    party.user_id = user.id
    if not party.email:
        party.email = email_norm
    if phone and not party.phone:
        party.phone = phone
    return user


def unlink_portal_login(db: Session, *, vendor_id: int, party: Customer) -> int | None:
    """Detach portal user from party. Returns previous user_id if any."""
    if not party.user_id:
        return None
    prev = party.user_id
    party.user_id = None
    user = db.get(User, prev)
    if user and user.vendor_id == vendor_id and user.role in PORTAL_ROLES:
        # Keep account but mark inactive so orphan logins cannot use B2B/store until re-linked
        user.status = "DISABLED"
    return prev


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
