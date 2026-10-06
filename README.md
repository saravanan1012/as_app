# AS App (multi-vendor)

New monorepo for **Nuxt UI + FastAPI + PostgreSQL** multi-vendor ERP / storefront.

| Path | Purpose |
|------|---------|
| `docs/phase-0/` | Phase 0 contracts (frozen before Phase 1 code) |
| `frontend/` | Nuxt app (Phase 1+) |
| `backend/` | FastAPI app (Phase 1+) |
| `scripts/` | Deploy / ETL helpers |
| `.github/workflows/` | CI/CD (updated in Phase 8; target design in Phase 0) |

**Legacy reference (read-only during strangler):** `/home/saravanan/Videos/learn/rjs/as`

**Plans:**
- [Nuxt FastAPI Migration](/home/saravanan/.cursor/plans/nuxt_fastapi_migration_47720978.plan.md)
- [Schema Gaps](/home/saravanan/.cursor/plans/schema_gaps_multi-vendor_675e8c8d.plan.md)

## Theme

Default: **Matte Gold**. Other gold palettes (Rose / Deep / Vibrant) are defined for later switching — see [docs/phase-0/themes.md](docs/phase-0/themes.md).

## Status

- **Phases 0–10:** COMPLETE — contracts → API → Store → Nuxt admin → cutover → hardening → B2B trade portal
- Docs: `docs/phase-0/` … `docs/phase-10/`

```bash
# Dev
docker compose up -d --build
# Web: http://localhost:3000  ·  API: http://localhost:8000/api/health

# Prod-shaped (needs .env.prd)
cp .env.prd.example .env.prd   # edit secrets
make up-prd                    # web on :3001

# login: superadmin@as.com / User@123  (demo SKUs: DEMO-*)
# B2B hierarchy (all password User@123):
#   distributor@as.com → dealer@as.com → retailer@as.com → retail-customer@as.com
#   also: distributor2 / dealer2-3 / retailer2-3 / customer2-3 / direct@as.com
docker compose exec -T api pytest -q
```


VPS setup: [docs/vps-setup.md](docs/vps-setup.md) · Cutover: [docs/phase-8/retire-legacy.md](docs/phase-8/retire-legacy.md) · Ops: [docs/phase-9/runbook.md](docs/phase-9/runbook.md)

