# Phase 8 — Cutover (COMPLETE)

Production deploy path for Nuxt + FastAPI + Postgres. Replaces legacy Next/MySQL deploy root.

## Artifacts

| Path | Purpose |
|------|---------|
| `docker-compose.prd.yml` | Prod compose — db (internal), api (internal), web **3001:3000** |
| `.env.prd.example` | Env template → copy to VPS as `.env.prd` |
| `deploy/nginx/as.hindupanjang.com.conf.example` | Same-origin Nginx notes |
| `scripts/deploy-production.sh` | Build/up + health (`/` + `/api/health`) |
| `.github/workflows/deploy.yml` | SSH deploy to `/root/projects/production/as_app` |
| `Makefile` | `make up` / `up-prd` / `api-test` / `etl-dry` |
| `scripts/etl/` | MySQL → Postgres core migration helper |
| `frontend/capacitor.config.ts` | Default server URL → production HTTPS |

## VPS first-time

**Full step-by-step:** [../vps-setup.md](../vps-setup.md) (stop Next → clone → `.env.prd` → deploy → smoke → ETL → Actions).

```bash
# Short path (details in vps-setup.md)
mkdir -p /root/projects/production/as_app && cd /root/projects/production/as_app
git clone <as_app-remote> .
cp .env.prd.example .env.prd   # edit secrets
bash scripts/deploy-production.sh
```

GitHub Actions secrets (same pattern as legacy): `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`.

## Same-origin / Nginx

**No port change required.** Live VPS config already proxies `https://as.hindupanjang.com` → `http://94.249.213.162:3001`.

After cutover, that `:3001` process is `as_app_web` (Nuxt) instead of Next. Canonical copy of the site file: [`deploy/nginx/as.hindupanjang.com.conf.example`](../../deploy/nginx/as.hindupanjang.com.conf.example).

```
Browser / Capacitor
  → Nginx :443 (as.hindupanjang.com)
  → host :3001 (as_app_web)
  → Nuxt proxies /api/** → api:8000 (Docker network)
```

`scripts/deploy-production.sh` rewrites `proxy_pass` to `AS_UPSTREAM_URL` (default `http://94.249.213.162:3001`) and reloads Nginx when the site file exists.

## ETL

See [`scripts/etl/README.md`](../../scripts/etl/README.md). Run before pointing DNS/users at the new stack if you need catalog/customer data.

## Retire legacy

See [retire-legacy.md](./retire-legacy.md).

## Next

**Phase 9** — complete; see [phase-9/README.md](../phase-9/README.md).
