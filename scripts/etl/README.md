# MySQL → Postgres ETL (Phase 8)

Legacy app: `/home/saravanan/Videos/learn/rjs/as` (Prisma / MySQL).  
Target: `as_app` Postgres (`vendor_id` scoped).

## In scope (this helper)

| Legacy table | Target | Notes |
|--------------|--------|-------|
| `suppliers` | `suppliers` | `tenant_id` → `vendor_id` |
| `items` | `items` | Skip if code already exists for vendor |
| `customers` | `customers` | `type` → `party_type`; `ref_from` → `parent_id` |
| `customer_addresses` | `customer_addresses` | Remap customer ids |
| `users` (optional `--users`) | `users` | Staff only; copy bcrypt hash |

## Out of scope (manual / later)

- Sale / purchase orders, GRN, stock ledger, Razorpay payment events  
- Offers / reviews (recreate or extend script)  
- Images on disk (`storage/`) — rsync separately  

## Setup

```bash
cd scripts/etl
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# From a host that can reach legacy MySQL + new Postgres:
export MYSQL_URL='mysql://app:app123@127.0.0.1:3307/app_staging'
export DATABASE_URL='postgresql://as:as_dev@127.0.0.1:5432/as_app'
export TARGET_VENDOR_ID=1

python migrate_core.py --dry-run
python migrate_core.py --apply
# optional staff users:
python migrate_core.py --apply --users
```

On VPS, tunnel or `docker network connect` so the ETL host can see both DBs. Prefer dumping MySQL to a file and restoring into a temporary container if the live DB must stay untouched.

## Party mapping

See [`docs/phase-0/party-hierarchy.md`](../../docs/phase-0/party-hierarchy.md):

- `type` uppercase → `party_type` (invalid → `CUSTOMER`)
- `ref_from = 0` → `parent_id` null
- `ref_from > 0` → mapped parent if present
- `acquisition_source` set to `OTHER` for imported rows

## After ETL

1. Confirm counts in admin UI / SQL.  
2. Set stock for online items (ledger starts empty).  
3. Set `SKIP_SEED=1` in `.env.prd` once bootstrap users exist.  
4. Enable Store from platform if needed.
