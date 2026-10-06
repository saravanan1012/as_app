# VPS setup — AS App (git clone → live)

Step-by-step production setup on the VPS for Nuxt + FastAPI + Postgres.

**Assumptions**

- Docker + Compose + Nginx already installed
- Site `as.hindupanjang.com` proxies to host `:3001` (`http://94.249.213.162:3001`)
- `as_app` is pushed to a git remote (`main`)
- Deploy path: `/root/projects/as_app`

Related: [phase-8/README.md](./phase-8/README.md) · [retire-legacy.md](./phase-8/retire-legacy.md) · [runbook.md](./phase-9/runbook.md)

---

## 0. Prerequisites (once)

- SSH as `root` (or a user in the `docker` group)
- Repo remote contains `docker-compose.prd.yml`, `scripts/deploy-production.sh`, `.env.prd.example`
- **Port 3001 free** before starting Nuxt (legacy Next must not bind it at the same time)

---

## 1. Stop legacy Next (frees `:3001`)

```bash
cd /root/projects/as
docker compose -f docker-compose.prd.yml --env-file .env.prd stop
# Do NOT use: docker compose down -v  (keeps MySQL volume for ETL/backup)
```

Optional MySQL backup first:

```bash
mkdir -p /root/backups
docker exec mysql-db-staging mysqldump -uapp -p'YOUR_PASS' --ssl-mode=DISABLED app_staging \
  | gzip > /root/backups/as_mysql_$(date +%F).sql.gz
```

---

## 2. Clone `as_app`

```bash
mkdir -p /root/projects/as_app
cd /root/projects/as_app
git clone <YOUR_AS_APP_GIT_URL> .
# e.g. git clone git@github.com:you/as_app.git .
git checkout main
```

---

## 3. Create production env

```bash
cp .env.prd.example .env.prd
nano .env.prd   # or vim
```

Set at least:

| Variable | Value |
|----------|--------|
| `POSTGRES_PASSWORD` | strong random |
| `DATABASE_URL` | `postgresql+psycopg2://as:<same-password>@db:5432/as_app` |
| `AUTH_SECRET` | 32+ random chars |
| `AUTH_URL` | `https://as.hindupanjang.com` |
| `CORS_ORIGINS` | `https://as.hindupanjang.com` |
| `COOKIE_SECURE` | `true` |
| `NUXT_PUBLIC_APP_URL` | `https://as.hindupanjang.com` |
| `NUXT_PUBLIC_VENDOR_SLUG` | `as-demo` |
| `SKIP_SEED` | `0` on first boot (demo users / `DEMO-*` SKUs) |
| `RAZORPAY_MOCK` / keys | `false` + live keys when ready |

Never commit `.env.prd`. Template: [`.env.prd.example`](../.env.prd.example).

---

## 4. Nginx (usually no change)

Existing production config already has:

```nginx
proxy_pass http://94.249.213.162:3001;
```

Optional refresh from the repo (keeps Certbot SSL paths):

```bash
cp /root/projects/as_app/deploy/nginx/as.hindupanjang.com.conf.example \
   /etc/nginx/sites-available/as.hindupanjang.com
nginx -t && systemctl reload nginx
```

Canonical example: [`deploy/nginx/as.hindupanjang.com.conf.example`](../deploy/nginx/as.hindupanjang.com.conf.example).

Traffic path:

```
Browser / Capacitor
  → Nginx :443 (as.hindupanjang.com)
  → host :3001 (as_app_web / Nuxt)
  → Nuxt proxies /api/** → api:8000 (Docker network)
```

---

## 5. First deploy (build + up + health)

```bash
cd /root/projects/as_app
chmod +x scripts/deploy-production.sh
bash scripts/deploy-production.sh
```

This will:

1. `git pull` on `main`
2. Ensure Nginx `proxy_pass` → `AS_UPSTREAM_URL` (default `http://94.249.213.162:3001`)
3. `docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build`
4. Health-check `/` and `/api/health`

Manual equivalent:

```bash
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d --build
docker compose -f docker-compose.prd.yml --env-file .env.prd ps
curl -fsS http://94.249.213.162:3001/
curl -fsS http://94.249.213.162:3001/api/health
curl -fsS https://as.hindupanjang.com/
curl -fsS https://as.hindupanjang.com/api/health
```

Expect containers: `as_app_db`, `as_app_api`, `as_app_web`.

---

## 6. Smoke test in browser

1. `https://as.hindupanjang.com/` — landing + gallery  
2. Login `superadmin@as.com` / `User@123` → `/platform` → enable **Store**  
3. `/store` — demo SKUs (`DEMO-*`) or ETL data  
4. `admin@as.com` / `User@123` → `/admin` — items / sales  

After first successful boot, set `SKIP_SEED=1` in `.env.prd` so the API entrypoint only runs migrations:

```bash
# edit .env.prd → SKIP_SEED=1
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d api
```

---

## 7. Optional: MySQL → Postgres ETL

If you need legacy catalog / customers, see [`scripts/etl/README.md`](../scripts/etl/README.md).

```bash
cd /root/projects/as_app/scripts/etl
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export MYSQL_URL='mysql://app:PASS@127.0.0.1:PORT/app_staging'
export DATABASE_URL='postgresql://as:PASS@127.0.0.1:5432/as_app'
export TARGET_VENDOR_ID=1

python migrate_core.py --dry-run
python migrate_core.py --apply
# optional staff users:
python migrate_core.py --apply --users
```

Postgres is not published on the host by default — use a one-off publish, `docker network connect`, or `docker exec` + dump/restore as needed. Online items may still need stock adjusted after ETL.

---

## 8. GitHub Actions (ongoing deploys)

On the **as_app** repository:

| Item | Value |
|------|--------|
| Workflow | `.github/workflows/deploy.yml` |
| Secrets | `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS` |
| Remote path | `/root/projects/as_app` |

Disable the legacy **Deploy as** workflow on `learn/rjs/as` so it does not fight for `:3001`.

---

## 9. Do not

- Run `docker compose down -v` on the VPS (destroys Postgres / uploads volumes)
- Run Next and Nuxt both on `:3001`
- Leave `AUTH_URL` / `NUXT_PUBLIC_APP_URL` as `http://localhost…` (deploy script refuses this)

---

## Rollback

```bash
cd /root/projects/as_app
docker compose -f docker-compose.prd.yml --env-file .env.prd stop

cd /root/projects/as
docker compose -f docker-compose.prd.yml --env-file .env.prd up -d
# Nginx still points at :3001 → Next again (if MySQL volume intact)
```

---

## Order summary

1. Stop Next  
2. Clone `as_app`  
3. Create `.env.prd`  
4. Confirm Nginx → `:3001`  
5. `bash scripts/deploy-production.sh`  
6. Smoke test  
7. Optional ETL  
8. Wire Actions + retire legacy workflow  
