# Phase 0 — Contracts (complete before Phase 1)

**Repo root:** `/home/saravanan/Videos/projects/as_app`  
**Legacy app:** `/home/saravanan/Videos/learn/rjs/as`  
**Rule:** No Phase 1 application code until these contracts are accepted.

| Document | Freeze |
|----------|--------|
| [openapi-conventions.md](./openapi-conventions.md) | API envelope, errors, auth headers |
| [rbac-matrix.md](./rbac-matrix.md) | Role → resource.action permissions |
| [party-hierarchy.md](./party-hierarchy.md) | DISTRIBUTOR / DEALER / CUSTOMER + sources |
| [vendor-settings.md](./vendor-settings.md) | JSONB settings incl. `store_enabled` |
| [ux-ia.md](./ux-ia.md) | Landing, Store menu, login redirects, shells |
| [themes.md](./themes.md) | Matte Gold default + alternate gold themes |
| [docker-and-ci.md](./docker-and-ci.md) | Compose (Postgres/API/Nuxt) + GitHub Actions target |

## Exit criteria

- [x] Documents written under `docs/phase-0/`
- [x] Default theme = Matte Gold; others reserved for switch
- [x] Docker + GitHub Actions target design documented
- [x] Parent/child plans updated with repo path + DevOps
- [ ] Stakeholder acceptance (user) before Phase 1 coding

## Deferred (confirmed)

- Per-customer (not party-type) price overrides
- Live carrier tracking APIs (AKR / Maruthi)
- Postgres RLS, S3, marketplace settlements

**Delivered in Phase 10:** B2B portals, party price rules, qty-tier shipping, shipment tracking UI.
