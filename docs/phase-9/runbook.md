# Operations runbook (AS App)

## Health

| Check | Command / URL |
|-------|----------------|
| API | `GET /api/health` |
| Web | `GET /` |
| Through Nuxt proxy | `GET /api/health` on the public origin |

```bash
curl -fsS https://as.hindupanjang.com/api/health
curl -fsS https://as.hindupanjang.com/
docker compose -f docker-compose.prd.yml --env-file .env.prd ps
```

## Deploy

```bash
cd /root/projects/as_app
bash scripts/deploy-production.sh
# or: push to main → GitHub Actions Deploy as_app
```

Never: `docker compose down -v` on VPS.

## Secrets rotation

1. Generate new `AUTH_SECRET` (32+ random chars) and `POSTGRES_PASSWORD`.
2. Update `.env.prd` `DATABASE_URL` password to match.
3. `docker compose -f docker-compose.prd.yml --env-file .env.prd up -d` (api recreates sessions — users re-login).
4. Rotate Razorpay keys in dashboard + `.env.prd`; set `RAZORPAY_MOCK=false`.
5. Rotate GitHub `SSH_PRIVATE_KEY` if compromised; update `SSH_KNOWN_HOSTS` if host key changes.

## Backups

```bash
# Postgres dump (from host with docker)
docker exec as_app_db pg_dump -U as as_app | gzip > as_app_$(date +%F).sql.gz
# Uploads volume
docker run --rm -v as_app_as_uploads:/data -v "$PWD":/backup alpine \
  tar czf /backup/uploads_$(date +%F).tgz -C /data .
```

Restore: stop api/web, restore dump into empty DB, restore uploads volume, `up -d`.

## Common incidents

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `/store` redirects home | `store_enabled` false | Platform → Store toggle |
| 403 on `/api/store/*` | Same | Toggle + check `x-vendor-slug` |
| Empty store catalog | No online items / stock | Seed `DEMO-*` or admin Items + Stock |
| Login cookie missing on HTTPS | `COOKIE_SECURE` false behind HTTPS | Set `COOKIE_SECURE=true` |
| SUPER_ADMIN 400 on `/api/items` | Missing `vendor_id` | Platform → Open admin |
| Web up, API 502 via `/api` | api container down | `docker logs as_app_api` |
| Deploy health fails on curl | VPS `127.0.0.1:3001` quirk | Use public IP upstream (deploy script default) |

## Seed control

- Dev: entrypoint runs seed (idempotent).
- Prod after ETL: `SKIP_SEED=1` in `.env.prd`.

## Capacitor

```bash
CAPACITOR_SERVER_URL=https://as.hindupanjang.com npm run cap:sync
# local:
CAPACITOR_SERVER_URL=http://localhost:3001 CAPACITOR_CLEARTEXT=true …
```
