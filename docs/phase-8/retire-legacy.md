# Retire legacy Next / MySQL deploy

Do this **after** Phase 8 UAT on `as_app` (Store + admin smoke on the new stack).

## Checklist

1. **Freeze writes** on legacy (maintenance window) if ETL must be final.
2. Run `scripts/etl/migrate_core.py --apply` (and stock/media as needed).
3. Deploy `as_app` to `/root/projects/production/as_app` with `.env.prd`.
4. Confirm health: `https://as.hindupanjang.com/` and `/api/health`.
5. Confirm Store + login + one COD order + admin SO list.
6. **Disable legacy GitHub Actions** on `learn/rjs/as`:
   - Pause or delete `.github/workflows/deploy.yml` in that repo, **or**
   - Rename workflow / protect branch so pushes no longer deploy Next.
7. Stop legacy containers (do **not** remove volumes until backup verified):

```bash
cd /root/projects/as
docker compose -f docker-compose.prd.yml --env-file .env.prd stop
# Keep volumes: staging_mysql_data — backup with mysqldump before `down -v`
```

8. **Nginx stays on `:3001`** — your existing `proxy_pass http://94.249.213.162:3001` keeps working; after cutover that port is Nuxt (`as_app_web`), not Next. Reference: `deploy/nginx/as.hindupanjang.com.conf.example`.
9. Capacitor: rebuild with `CAPACITOR_SERVER_URL=https://as.hindupanjang.com`.
10. Document rollback: start legacy compose again and keep the same Nginx upstream if you still bind Next to `:3001` (MySQL volume must still exist).

## Do not

- Run `docker compose down -v` on either stack until backups are confirmed.
- Point both Next and Nuxt at the same host port simultaneously.
- Leave two `deploy.yml` workflows fighting for the same VPS path.
