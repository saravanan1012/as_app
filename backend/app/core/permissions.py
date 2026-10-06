"""RBAC seed matrix — see docs/phase-0/rbac-matrix.md"""

ROLES = (
    "SUPER_ADMIN",
    "ADMIN",
    "MANAGER",
    "STAFF",
    "DISTRIBUTOR",
    "DEALER",
    "RETAILER",
    "CUSTOMER",
)

ALL_PERMISSIONS: list[tuple[str, str]] = [
    ("platform.vendors.manage", "Create/suspend vendors, settings, store toggle"),
    ("dashboard.read", "Vendor dashboard"),
    ("catalog.items.read", "Read catalog items"),
    ("catalog.items.write", "Create/update catalog items"),
    ("catalog.items.manage", "Manage catalog items"),
    ("stock.read", "Read stock"),
    ("stock.write", "Adjust stock"),
    ("stock.manage", "Manage stock"),
    ("sales.orders.read", "Read sales orders"),
    ("sales.orders.write", "Create/update sales orders"),
    ("sales.orders.manage", "Manage sales orders"),
    ("purchase.orders.read", "Read purchase orders"),
    ("purchase.orders.write", "Create/update purchase orders"),
    ("purchase.orders.manage", "Manage purchase orders"),
    ("customers.read", "Read customers"),
    ("customers.write", "Create/update customers"),
    ("customers.manage", "Manage customers"),
    ("suppliers.read", "Read suppliers"),
    ("suppliers.write", "Create/update suppliers"),
    ("offers.read", "Read offers"),
    ("offers.write", "Create/update offers"),
    ("ecommerce.store.read", "Access store APIs when enabled"),
    ("b2b.portal", "Access B2B trade portal"),
    ("b2b.downline.read", "Read downline parties"),
    ("b2b.orders.read", "Read B2B / scoped sale orders"),
    ("b2b.orders.write", "Create B2B sale orders for downline"),
    ("users.read", "Read users"),
    ("users.write", "Create/update users"),
    ("users.manage", "Manage users"),
    ("transactions.read", "Read transactions"),
    ("transactions.write", "Write transactions"),
    ("audit.read", "Read audit logs"),
    ("activities.read", "Read activities"),
    ("activities.write", "Write activities"),
]

_TRADE_PERMS = [
    "b2b.portal",
    "b2b.downline.read",
    "b2b.orders.read",
    "b2b.orders.write",
    "ecommerce.store.read",
]

# role -> list of permission codes (expand * for manage/write/read as in matrix)
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "SUPER_ADMIN": [code for code, _ in ALL_PERMISSIONS],
    "ADMIN": [
        "dashboard.read",
        "catalog.items.manage",
        "catalog.items.write",
        "catalog.items.read",
        "stock.manage",
        "stock.write",
        "stock.read",
        "sales.orders.manage",
        "sales.orders.write",
        "sales.orders.read",
        "purchase.orders.manage",
        "purchase.orders.write",
        "purchase.orders.read",
        "customers.manage",
        "customers.write",
        "customers.read",
        "suppliers.write",
        "suppliers.read",
        "offers.write",
        "offers.read",
        "ecommerce.store.read",
        "b2b.portal",
        "b2b.downline.read",
        "b2b.orders.read",
        "b2b.orders.write",
        "users.manage",
        "users.write",
        "users.read",
        "transactions.write",
        "transactions.read",
        "audit.read",
        "activities.write",
        "activities.read",
    ],
    "MANAGER": [
        "dashboard.read",
        "catalog.items.write",
        "catalog.items.read",
        "stock.write",
        "stock.read",
        "sales.orders.write",
        "sales.orders.read",
        "purchase.orders.write",
        "purchase.orders.read",
        "customers.write",
        "customers.read",
        "suppliers.write",
        "suppliers.read",
        "offers.write",
        "offers.read",
        "ecommerce.store.read",
        "b2b.orders.read",
        "users.read",
        "transactions.write",
        "transactions.read",
        "audit.read",
        "activities.write",
        "activities.read",
    ],
    "STAFF": [
        "dashboard.read",
        "catalog.items.read",
        "stock.read",
        "sales.orders.write",
        "sales.orders.read",
        "purchase.orders.read",
        "customers.write",
        "customers.read",
        "suppliers.read",
        "offers.read",
        "ecommerce.store.read",
        "transactions.read",
        "activities.write",
        "activities.read",
    ],
    "DISTRIBUTOR": list(_TRADE_PERMS),
    "DEALER": list(_TRADE_PERMS),
    "RETAILER": list(_TRADE_PERMS),
    "CUSTOMER": [
        "ecommerce.store.read",
        "b2b.orders.read",
    ],
}


def permission_implies(have: set[str], needed: str) -> bool:
    """manage implies write+read; write implies read for same resource."""
    if needed in have:
        return True
    parts = needed.rsplit(".", 1)
    if len(parts) != 2:
        return False
    resource, action = parts
    if action == "read":
        return f"{resource}.write" in have or f"{resource}.manage" in have
    if action == "write":
        return f"{resource}.manage" in have
    return False
