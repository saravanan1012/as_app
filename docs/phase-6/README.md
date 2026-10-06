# Phase 6 — Nuxt public + Store (COMPLETE)

Mobile-first Nuxt 4 + Nuxt UI front-end: company landing, product info, Store when enabled, login redirect, Capacitor URL stub.

## Stack

- `frontend/` — Nuxt 4, Nuxt UI 4, Pinia, Matte Gold theme (Fraunces + Source Sans 3)
- API proxy: Nitro ` /api/**` → FastAPI (`NUXT_API_PROXY`)
- Vendor context: `x-vendor-slug` (default `as-demo`)

## Public API (no Store gate)

| Path | Purpose |
|------|---------|
| `GET /api/public/vendor` | Branding + `store_enabled` |
| `GET /api/public/products` | Sellable product info |
| `GET /api/public/products/{id}` | Product detail |

## Front-end routes

| Path | Notes |
|------|--------|
| `/` | Brand-first full-bleed hero + product highlights (not cart) |
| `/products`, `/products/:id` | Info pages; Add-to-cart only if Store on + online item |
| `/contact`, `/login` | Contact + RBAC-aware redirect |
| `/store/**` | Catalog, cart, checkout (COD / mock Razorpay), orders, register |
| `/admin/**`, `/platform/**` | See [Phase 7](../phase-7/README.md) |

Store middleware: if `store_enabled` is false → redirect `/`.

## Docker

```bash
docker compose up -d --build
# Web  http://localhost:3000
# API  http://localhost:8000/api/docs
```

Enable Store (superadmin), then open `/store`:

```bash
curl -c /tmp/as.ck -X POST http://localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"superadmin@as.com","password":"User@123"}'
curl -b /tmp/as.ck -X PATCH http://localhost:8000/api/platform/vendors/1/store \
  -H 'content-type: application/json' -d '{"store_enabled":true}'
```

## Local Nuxt (hot reload)

```bash
docker compose up -d db api
cd frontend && npm install
NUXT_API_PROXY=http://localhost:8000 npm run dev
```

## Capacitor

`frontend/capacitor.config.ts` — set `CAPACITOR_SERVER_URL` to the Nuxt origin when packaging.

## Next

**Phase 7** — complete; see [phase-7/README.md](../phase-7/README.md).
