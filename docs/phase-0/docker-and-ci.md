# Docker and GitHub Actions (target design)

Legacy today ([learn/rjs/as](/home/saravanan/Videos/learn/rjs/as)):

- Single Next.js `Dockerfile` + MySQL 8.4 in `docker-compose.prd.yml` (host port **3001**)
- Deploy: `.github/workflows/deploy.yml` → SSH → `scripts/deploy-production.sh` on VPS (`/root/projects/as`)

**New target** lives in this monorepo (`as_app`). Implement Compose/Dockerfiles in Phase 1 (dev) and harden in Phase 8 (prod cutover). Update GHA when `as_app` is the deploy root.

## Target Compose services

```yaml
# Conceptual — implement in Phase 1/8
services:
  db:          # postgres:16
  api:         # FastAPI (uvicorn) — internal :8000
  web:         # Nuxt (node) — internal :3000
  # optional migrate job / api entrypoint: alembic upgrade head
```

| Service | Image / build | Host publish (prod pattern) |
|---------|---------------|-----------------------------|
| `db` | `postgres:16-alpine` | **not published** (Docker network only) |
| `api` | `backend/Dockerfile` | internal; Nginx → `/api` |
| `web` | `frontend/Dockerfile` | e.g. `3001:3000` **or** Nginx terminates TLS → web |

Volumes:

- `pg_data` → Postgres
- `uploads` → `api` at `/app/storage` (`storage/{vendor_id}/...`)

Env (names only): `DATABASE_URL`, `AUTH_SECRET`, `AUTH_URL`, `CORS`/`cookie` domain, `RAZORPAY_*`, `DEFAULT_VENDOR_ID`, `POSTGRES_*`.

## Dockerfiles (to add in Phase 1+)

1. **`backend/Dockerfile`** — multi-stage: deps → runtime (Python 3.12-slim), non-root user, `alembic upgrade` in entrypoint then uvicorn.
2. **`frontend/Dockerfile`** — multi-stage: `npm ci` → `nuxt build` → node runner (or Nitro preset node-server).
3. **Root `docker-compose.yml`** (dev) + **`docker-compose.prd.yml`** (prod) — replace MySQL/Next services.

Nginx (host or companion container):

- `/` → `web:3000`
- `/api` → `api:8000`
- Same origin for session cookies (required for Capacitor WebView)

## GitHub Actions — target workflow

File: `.github/workflows/deploy.yml` (replace legacy Next deploy when cutover).

```yaml
# Target shape (Phase 8) — not active until as_app is deploy root
name: Deploy as_app
on:
  push:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: as-app-production
  cancel-in-progress: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - name: Configure SSH
        # secrets: SSH_PRIVATE_KEY, SSH_KNOWN_HOSTS
      - name: Deploy
        env:
          SSH_HOST: <vps>
          SSH_PORT: <port>
          SSH_USER: root
          DEPLOY_PATH: /root/projects/as_app   # NEW path
        run: |
          ssh ... "cd $DEPLOY_PATH && git pull &&
            bash scripts/deploy-production.sh"
```

**`scripts/deploy-production.sh` (Phase 8):**

1. `docker compose -f docker-compose.prd.yml --env-file .env.prd pull/build`
2. Run migrations (`api` entrypoint or one-shot `migrate` service)
3. `up -d` web + api + db
4. Health checks: `GET /api/health`, `GET /`

Optional later job: **CI on PR** — `backend` pytest + ruff; `frontend` lint/build (add `.github/workflows/ci.yml` in Phase 1–2).

## Migration from legacy deploy

| Item | Legacy | New |
|------|--------|-----|
| Repo path on VPS | `/root/projects/as` | `/root/projects/as_app` |
| App container | Next standalone :3000 | Nuxt + FastAPI |
| DB | MySQL 8.4 | PostgreSQL 16 |
| Workflow | `Deploy as` | `Deploy as_app` |
| Host port | 3001→3000 | keep **3001** for web (or Nginx-only) to avoid colliding with other VPS apps |

Strangler option (Phase 5–7): temporary reverse-proxy path split (`/api` new, rest old) — only if dual-running; prefer full cutover after Phase 7 UAT.

## Phase mapping

| Phase | DevOps work |
|-------|-------------|
| 0 | This document (done) |
| 1 | Dev `docker-compose.yml` + backend Dockerfile + Postgres |
| 6–7 | Frontend Dockerfile; local full stack |
| 8 | Prod compose, Nginx examples, GHA + deploy script, retire legacy workflow |
| 9 | Health checks, secret rotation, runbook |

## Placeholders in this repo (Phase 0)

- `.github/workflows/` — empty until Phase 1/8 adds real YAML
- `scripts/` — add `deploy-production.sh` in Phase 8; may add stub README only in Phase 0
