# OpenAPI / API conventions

Parity with legacy [`lib/route_handler.ts`](/home/saravanan/Videos/learn/rjs/as/lib/route_handler.ts) and [`ResponseHandler`](/home/saravanan/Videos/learn/rjs/as/src/utils/ResponseHandler.ts) — FastAPI must stay familiar to existing admin clients during strangler.

## Base URL

- Same origin: browser → `/api/...` (Nginx proxies to FastAPI)
- OpenAPI docs: `/api/docs` (dev/staging only if desired)

## Success envelope

```json
{
  "success": true,
  "message": "Sales fetched",
  "data": {}
}
```

- List endpoints may return `data` as array **or** `{ "data": [], "pagination": { "page", "pageSize", "total", "totalPages" } }` (match existing stocks/customers patterns).
- Create often returns `{ "id": ... }` inside `data`.

## Error envelope

```json
{
  "success": false,
  "message": "Human readable",
  "error": "optional detail",
  "data": null
}
```

HTTP status: `400` validation, `401` unauthenticated, `403` forbidden (RBAC or store disabled), `404` missing, `409` conflict, `500` unexpected.

## Auth

- Login: `POST /api/auth/login` → sets **httpOnly** JWT cookie (and may return non-secret user profile in body).
- Logout: `POST /api/auth/logout` clears cookie.
- Session: `GET /api/auth/me` → user + role + `vendor_id` + permission codes.
- Cookie name: `as_session` (freeze in Phase 1).
- Optional `Authorization: Bearer` for non-browser clients later; v1 cookie-first for Capacitor same-origin.

## Vendor context

Resolved in order:

1. Authenticated user's `vendor_id` (staff/customer of a vendor)
2. Header `x-vendor-slug`
3. Host subdomain slug
4. Path `/v/{slug}/...` (Nuxt passes slug to API)

Platform `SUPER_ADMIN` may pass `vendor_id` query/body when acting on a vendor.

## Permission failures

`403` with message `Forbidden` when role lacks `resource.action`.  
Store routes also `403`/`404` when `settings.features.store_enabled` is false.

## Versioning

No URL version prefix in v1 (`/api/...`). Breaking changes only via strangler until Next is retired.
