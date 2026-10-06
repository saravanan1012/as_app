# Frontend (Nuxt 4 + Nuxt UI)

Phase 6–7 — public landing, Store, vendor admin, platform console.

## Dev

```bash
# API running on :8000 (docker compose up -d api db)
npm install
NUXT_API_PROXY=http://localhost:8000 npm run dev
# → http://localhost:3000
```

Vendor slug header defaults to `as-demo` (`NUXT_PUBLIC_VENDOR_SLUG`).

## Routes

| Path | Notes |
|------|--------|
| `/` | Company landing (brand-first hero) |
| `/products`, `/products/:id` | Product info (no cart required) |
| `/contact`, `/login` | Contact + RBAC-aware redirect home |
| `/store/**` | Ecommerce — middleware redirects home if Store disabled |
| `/admin/**` | Vendor admin (RBAC nav); SUPER_ADMIN needs vendor via platform |
| `/platform/**` | SUPER_ADMIN vendors + Store toggle |

## Theme

Matte Gold tokens in `app/assets/css/main.css` — Fraunces + Source Sans 3.

## Capacitor

See `capacitor.config.ts` — default `server.url` is `https://as.hindupanjang.com`.  
Local: `CAPACITOR_SERVER_URL=http://localhost:3001 npm run cap:sync` (or similar).

Docs: [Phase 6](../docs/phase-6/README.md), [Phase 7](../docs/phase-7/README.md), [Phase 8](../docs/phase-8/README.md).

