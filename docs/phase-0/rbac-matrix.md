# RBAC matrix (role × resource.action)

Legacy app: binary `isAdminRole()` only — **replaced** by this matrix.

## Roles

| Role | Kind |
|------|------|
| `SUPER_ADMIN` | Platform staff (`vendor_id` null) |
| `ADMIN` | Vendor staff |
| `MANAGER` | Vendor staff |
| `STAFF` | Vendor staff |
| `DISTRIBUTOR` | B2B trade portal (Phase 10) |
| `DEALER` | B2B trade portal (Phase 10) |
| `RETAILER` | B2B trade portal (Phase 10) |
| `CUSTOMER` | Shop / account |

Trade portal permissions: `b2b.portal`, `b2b.downline.read`, `b2b.orders.read`, `b2b.orders.write` — see [docs/phase-10/README.md](../phase-10/README.md).

## Permission codes

Format: `{resource}.{action}` where action ∈ `read` | `write` | `manage`.

| Code | Meaning |
|------|---------|
| `platform.vendors.manage` | Create/suspend vendors, settings, store toggle |
| `dashboard.read` | Vendor dashboard |
| `catalog.items.read` / `.write` / `.manage` | Items + images + tax link |
| `stock.read` / `.write` / `.manage` | Stock, adjustments, movements view |
| `sales.orders.read` / `.write` / `.manage` | Sales orders, returns |
| `purchase.orders.read` / `.write` / `.manage` | PO, GRN, purchase returns |
| `customers.read` / `.write` / `.manage` | Trade parties + addresses |
| `suppliers.read` / `.write` | Suppliers |
| `offers.read` / `.write` | Coupons / offers |
| `ecommerce.store.read` | Access Store APIs when enabled (customers + public catalog rules) |
| `users.read` / `.write` / `.manage` | Vendor users |
| `transactions.read` / `.write` | Ledger |
| `audit.read` | Audit logs |
| `activities.read` / `.write` | Customer activities |

`manage` implies read+write plus destructive/admin ops (delete, suspend, seed).

## Seed grants

| Permission | SUPER_ADMIN | ADMIN | MANAGER | STAFF | CUSTOMER |
|------------|:-----------:|:-----:|:-------:|:-----:|:--------:|
| platform.vendors.manage | ✓ | | | | |
| dashboard.read | ✓ | ✓ | ✓ | ✓ | |
| catalog.items.* | ✓ | manage | write | read | |
| stock.* | ✓ | manage | write | read | |
| sales.orders.* | ✓ | manage | write | write | |
| purchase.orders.* | ✓ | manage | write | read | |
| customers.* | ✓ | manage | write | write | |
| suppliers.* | ✓ | write | write | read | |
| offers.* | ✓ | write | write | read | |
| ecommerce.store.read | ✓ | ✓ | ✓ | ✓ | ✓ |
| users.* | ✓ | manage | read | | |
| transactions.* | ✓ | write | write | read | |
| audit.read | ✓ | ✓ | ✓ | | |
| activities.* | ✓ | write | write | write | |

CUSTOMER additionally scoped in handlers to **own** `customer_id` / orders (not full `customers.read`).

## Post-login redirect (Nuxt)

1. Has `platform.vendors.manage` → `/platform`
2. Has `sales.orders.write` and not `purchase.orders.write` → `/admin/sales-orders`
3. Has `purchase.orders.write` and not `sales.orders.write` → `/admin/purchase-orders`
4. Any other vendor staff permission → `/admin/sales-orders`
5. Else if vendor `store_enabled` → `/store`
6. Else → `/`

## Enforcement

- FastAPI: `Depends(require_permission("sales.orders.write"))`
- Nuxt: hide menu items without permission; middleware on `/admin/**` and `/platform/**`
- Store: `store_enabled` **and** public/customer access rules
