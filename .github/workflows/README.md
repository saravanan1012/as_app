# GitHub Actions

| Workflow | When |
|----------|------|
| `ci.yml` | PR / push `main` — backend pytest (+ optional frontend build) |
| `deploy.yml` | Push `main` / manual — SSH → `/root/projects/as_app` → `scripts/deploy-production.sh` |

**Secrets for deploy:** `SSH_PRIVATE_KEY`, `SSH_KNOWN_HOSTS`.

VPS must have the repo cloned at `/root/projects/as_app` with `.env.prd` present before the first Actions run.

Design: [`docs/phase-0/docker-and-ci.md`](../../docs/phase-0/docker-and-ci.md). Cutover: [`docs/phase-8/README.md`](../../docs/phase-8/README.md).

Disable the **legacy** `Deploy as` workflow on `learn/rjs/as` after cutover — see [`docs/phase-8/retire-legacy.md`](../../docs/phase-8/retire-legacy.md).
