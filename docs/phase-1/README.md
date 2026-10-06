# Phase 1 — Backend foundation (COMPLETE)

## Delivered

- FastAPI app under `backend/app`
- Postgres 16 via root `docker-compose.yml` (`db` + `api` on **:8000**)
- Alembic migration `20261005_0001` — vendors, users, permissions, role_permissions, locations, items, item_images, stock, stock_movements
- JWT httpOnly cookie `as_session`
- RBAC seed matrix + `require_permission`
- Vendor context (session / `x-vendor-slug` / host / default)
- Seed: SUPER_ADMIN + 2 vendors + admins/staff
- Minimal platform vendor list/create
- Isolation check endpoint + pytest
- `.github/workflows/ci.yml`

## Verify

```bash
cd /home/saravanan/Videos/projects/as_app
docker compose up -d --build
curl -s http://localhost:8000/api/health
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"superadmin@as.com","password":"User@123"}'
docker compose exec -T api pytest -q
```

Docs: http://localhost:8000/api/docs

## Next

**Phase 2** — full super-admin vendor platform APIs (settings PATCH, store_enabled, bootstrap admin, dashboard).
