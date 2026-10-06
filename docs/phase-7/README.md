# Phase 7 — Nuxt vendor admin + platform (COMPLETE)

RBAC-filtered admin console and SUPER_ADMIN platform (Store toggle, vendor bootstrap). Client-side sale invoice PDF (jsPDF).

## Scope

| Area | Routes |
|------|--------|
| Platform | `/platform` vendors list + Store switch, `/platform/vendors/new`, `/platform/vendors/:id` |
| Admin shell | Layout + nav from `useAdminNav` (permission-gated) |
| Core ops | Dashboard, sales/purchase orders (+ GRN), items, stock (balances/ledger/adjust), suppliers, offers |
| Parties | Customers hierarchy UI (Distributor → Dealer → Customer), acquisition filters |
| Ops | Transactions, users, audit |
| Invoice | `utils/invoicePdf.ts` — download from sale order detail |

## SUPER_ADMIN vendor context

Platform **Open admin** sets `adminContext.vendorId`. `useApi` appends `?vendor_id=` for SUPER_ADMIN calls into vendor-scoped APIs.

## Middleware

- `admin` — staff roles or SUPER_ADMIN with vendor selected; else redirect `/login` or `/platform`
- `platform` — SUPER_ADMIN only

## Redirect homes (login)

| Role | Home |
|------|------|
| SUPER_ADMIN | `/platform` |
| ADMIN / MANAGER / STAFF | `/admin` |
| CUSTOMER | `/store` or `/` |

## Verify

```bash
cd frontend && npm run build
# or full stack
docker compose up -d --build
```

Smoke: login as `superadmin@as.com` → platform Store toggle → Open admin → customers / SO / invoice PDF.

## Next

**Phase 8** — complete; see [phase-8/README.md](../phase-8/README.md).
**Phase 9** — hardening / deeper tests.
