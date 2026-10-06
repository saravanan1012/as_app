# Phase 5 — Ecommerce / Store APIs (COMPLETE)

Store catalog, checkout (COD + Razorpay), offers, payment events, reviews, uploads — all gated on `vendors.settings.features.store_enabled`.

## Migration

`20261005_0004` — `offer_redemptions`, `payment_events`, `item_reviews` (`is_verified_purchase`); partial unique on `sale_orders(vendor_id, razorpay_payment_id)`.

## Store gate

- Resolve vendor via `x-vendor-slug` (or host / default vendor).
- If `features.store_enabled` is false → **403** `Store is disabled`.
- Landing / product **info** (non-cart) stays out of this gate (Nuxt Phase 6).

## APIs (`/api/store/*`)

| Path | Auth | Notes |
|------|------|-------|
| `POST /auth/register` | public | Creates `CUSTOMER` user + party, sets cookie |
| `GET /meta` | public | Branding + feature flags |
| `GET /products`, `GET /products/{id}` | public | Online sellable items + available qty |
| `POST /offers/validate` | optional | party_type / channel / max_uses |
| `POST /checkout/cod` | cookie | Deducts stock immediately |
| `POST /checkout/razorpay/create` | cookie | Reserves stock; returns Razorpay order |
| `POST /checkout/razorpay/verify` | cookie | Idempotent via `payment_events` |
| `POST /checkout/razorpay/webhook` | signature | Captured payments |
| `GET /checkout/razorpay/mock-sign` | public | Dev/CI only when `RAZORPAY_MOCK=true` |
| `GET/POST /products/{id}/reviews` | read / cookie | Verified purchase when prior SO |
| `GET /my-orders` | cookie | Ecommerce orders for linked customer |

Staff uploads: `POST /api/uploads/items/{id}/images` (`catalog.items.write`).

## Payments

| Mode | Stock | Payment status |
|------|-------|----------------|
| COD | Deduct on create | `UNPAID` |
| Razorpay | `quantity_reserved` until verify | `UNPAID` → `PAID` (then consume reservation + ledger) |

Env: `RAZORPAY_MOCK` (default true), `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`. Vendor settings may override key id / secret ref.

## Shipping

From `settings.shipping.flat_rate` / `free_over`; offer `free_shipping` zeroes charge.

## Verify

```bash
docker compose up -d --build
docker compose exec api pytest -q
```

Enable store (superadmin):

```bash
curl -c /tmp/as.ck -X POST http://localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"superadmin@as.com","password":"User@123"}'
curl -b /tmp/as.ck -X PATCH http://localhost:8000/api/platform/vendors/1/store \
  -H 'content-type: application/json' -d '{"store_enabled":true}'
curl -H 'x-vendor-slug: as-demo' http://localhost:8000/api/store/meta
```

## Next

**Phase 6** — Nuxt public landing + Store UI — see `../phase-6/README.md`.
