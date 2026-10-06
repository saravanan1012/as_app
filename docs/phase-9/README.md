# Phase 9 — Hardening (COMPLETE)

Final hardening for v1: tests, demo seed, secrets hygiene, ops runbook, responsive QA checklist.

## What landed

| Area | Detail |
|------|--------|
| Tests | `backend/tests/test_phase9_hardening.py` — RBAC denials, cross-vendor isolation, hierarchy, store gate vs public, checkout idempotency, login redirects, demo catalog |
| Seed | `DEMO-*` online items + stock for `as-demo`; `manager@as.com` |
| Secrets | Expanded `.env.example` / `.env.prd.example`; prod `SKIP_SEED` |
| Docs | This README + [runbook.md](./runbook.md) + [responsive-qa.md](./responsive-qa.md) |

## Verify

```bash
docker compose up -d db api
docker compose exec -T api pytest -q
# or locally with DATABASE_URL pointing at Postgres
cd backend && pytest -q
```

## Demo accounts (password `User@123`)

| Email | Role | Home |
|-------|------|------|
| `superadmin@as.com` | SUPER_ADMIN | `/platform` |
| `admin@as.com` | ADMIN | `/admin` |
| `manager@as.com` | MANAGER | `/admin` |
| `staff@as.com` | STAFF | `/admin` |
| `admin2@as.com` | ADMIN (vendor-two) | `/admin` |

Enable Store → `/platform` → toggle Store → shop demo SKUs at `/store`.

## App complete (phases 0–9)

Product surface for v1 is done. Remaining work is operational (real VPS cutover, live Razorpay keys, Capacitor store builds) — see [runbook.md](./runbook.md) and [phase-8/retire-legacy.md](../phase-8/retire-legacy.md).
