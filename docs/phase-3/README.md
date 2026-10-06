# Phase 3 — Vendor-scoped CRUD + party hierarchy (COMPLETE)

## Migration

`20261005_0002` — customers (+ hierarchy), addresses, suppliers, tax_categories, offers, transactions, activities, audit_logs; `items.tax_category_id`.

## APIs (vendor-scoped; staff cookie; SUPER_ADMIN uses `?vendor_id=`)

| Resource | Paths | Permission |
|----------|-------|------------|
| Customers | `/api/customers` | `customers.*` |
| Items | `/api/items` | `catalog.items.*` |
| Locations | `/api/locations` | `stock.*` |
| Stock | `/api/stock` | `stock.*` |
| Tax categories | `/api/tax-categories` | `catalog.items.*` |
| Suppliers | `/api/suppliers` | `suppliers.*` |
| Offers | `/api/offers` | `offers.*` |
| Users | `/api/users` | `users.*` |
| Transactions | `/api/transactions` | `transactions.*` |
| Activities | `/api/activities` | `activities.*` |
| Audit logs | `/api/audit-logs` | `audit.read` |
| Vendor dashboard | `/api/dashboard` | `dashboard.read` |

## Party hierarchy

- Types: `DISTRIBUTOR` → `DEALER` → `CUSTOMER`
- Independent: `parent_id` null + `acquisition_source` (`ONLINE`, `FB_LEAD`, …)
- Filters: `?party_type=&acquisition_source=&parent_id=&search=`

## Next

**Phase 4** — PO / SO / GRN / stock movements / GST — see `../phase-4/README.md`.
