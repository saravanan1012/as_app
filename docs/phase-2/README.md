# Phase 2 — Platform vendor APIs (COMPLETE)

Super-admin (`platform.vendors.manage`) can fully configure vendors.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/platform/dashboard` | Aggregates + per-vendor summary |
| GET | `/api/platform/vendors` | List vendors |
| POST | `/api/platform/vendors` | Create (+ optional admin, MAIN location, storage dir) |
| GET | `/api/platform/vendors/{id}` | Detail + `storage_path` |
| PATCH | `/api/platform/vendors/{id}` | name/plan/status/gstin/… |
| PATCH | `/api/platform/vendors/{id}/settings` | Deep-merge JSONB settings |
| PATCH | `/api/platform/vendors/{id}/store` | `{ "store_enabled": true\|false }` |
| POST | `/api/platform/vendors/{id}/bootstrap-admin` | Create/reset vendor ADMIN/MANAGER |
| POST | `/api/platform/vendors/{id}/suspend` | Suspend |
| POST | `/api/platform/vendors/{id}/activate` | Activate |

## Storage convention

`storage/{vendor_id}/` (and `.../items/{item_id}/` helper for later uploads).

## Example

```bash
# login as superadmin@as.com / User@123
curl -c /tmp/as.ck -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"superadmin@as.com","password":"User@123"}'

curl -b /tmp/as.ck -X PATCH http://localhost:8000/api/platform/vendors/1/store \
  -H 'Content-Type: application/json' \
  -d '{"store_enabled":true}'
```

## Next

**Phase 3** — vendor-scoped CRUD (customers with party hierarchy, catalog, stock, etc.).
