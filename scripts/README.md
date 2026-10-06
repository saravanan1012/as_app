# Scripts

| Script | Phase | Purpose |
|--------|-------|---------|
| `deploy-production.sh` | 8 | VPS deploy: compose build/up + health |
| `etl/migrate_core.py` | 8 | MySQL → Postgres (suppliers/items/customers) |
| `etl/README.md` | 8 | ETL runbook |

Never run `docker compose down -v` on production.

Docs: [`docs/phase-8/README.md`](../docs/phase-8/README.md), [`docs/phase-0/docker-and-ci.md`](../docs/phase-0/docker-and-ci.md).
