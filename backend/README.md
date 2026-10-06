# Backend (FastAPI + PostgreSQL)

Phase 1 foundation: vendors, users, RBAC, catalog/stock tables, JWT cookie auth.

## Quick start (Docker)

From repo root (`as_app/`):

```bash
docker compose up -d --build
curl -s http://localhost:8000/api/health
```

API docs: http://localhost:8000/api/docs

### Seeded users (password `User@123`)

| Email | Role |
|-------|------|
| superadmin@as.com | SUPER_ADMIN |
| admin@as.com | ADMIN (as-demo) |
| staff@as.com | STAFF (as-demo) |
| admin2@as.com | ADMIN (vendor-two) |

## Local (without Docker API)

```bash
# Postgres via compose
docker compose up -d db
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -c "from app.db import SessionLocal; from app.seed import run_seed; db=SessionLocal(); run_seed(db); db.close()"
uvicorn app.main:app --reload --port 8000
pytest -q
```

## Endpoints

### Phase 1
- `GET /api/health`
- `POST /api/auth/login` → httpOnly `as_session` cookie
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Phase 2 (platform — `platform.vendors.manage`)
- `GET /api/platform/dashboard`
- `GET/POST /api/platform/vendors`
- `GET/PATCH /api/platform/vendors/{id}`
- `PATCH /api/platform/vendors/{id}/settings`
- `PATCH /api/platform/vendors/{id}/store` — Store enable/disable
- `POST /api/platform/vendors/{id}/bootstrap-admin`
- `POST /api/platform/vendors/{id}/suspend|activate`

See `../docs/phase-2/README.md`.

### Phase 3 (vendor-scoped)
- `/api/customers` — party hierarchy (DISTRIBUTOR/DEALER/CUSTOMER)
- `/api/items`, `/api/locations`, `/api/stock`, `/api/tax-categories`
- `/api/suppliers`, `/api/offers`, `/api/users`
- `/api/transactions`, `/api/activities`, `/api/audit-logs`, `/api/dashboard`

See `../docs/phase-3/README.md`.

### Phase 4 (orders / GRN / GST / ledger)
- `/api/purchase-orders`, `/api/purchase-orders/{id}/receive`, `/api/goods-receipts`, `/api/purchase-returns`
- `/api/sale-orders` (+ confirm/cancel/events), `/api/sale-returns`
- `/api/stock-movements`, `/api/stock-adjustments`

See `../docs/phase-4/README.md`.

### Phase 5 (Store / ecommerce)
- `/api/store/*` — gated on `store_enabled` (header `x-vendor-slug`)
- Register, catalog, offer validate, COD + Razorpay checkout, reviews, my-orders
- `/api/uploads/items/{id}/images` — staff media upload

See `../docs/phase-5/README.md`.
