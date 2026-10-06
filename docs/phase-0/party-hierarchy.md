# Trade party hierarchy

Legacy: `customers.type` (free string) + `ref_from` (0 = none, no FK).

## Party types

| `party_type` | Description |
|--------------|-------------|
| `DISTRIBUTOR` | Top of optional channel |
| `DEALER` | Mid-tier; may hang under distributor or be independent |
| `RETAILER` | Retail trade party; under dealer/distributor or independent |
| `CUSTOMER` | End buyer; linked or independent |

## Hierarchy

```text
DISTRIBUTOR
  └── DEALER
        └── RETAILER
              └── CUSTOMER
DISTRIBUTOR
  └── RETAILER / CUSTOMER

Any party_type with parent_id NULL = independent (except DISTRIBUTOR stays top-only)
```

### Allowed parent edges

| Child | Allowed parent `party_type` |
|-------|----------------------------|
| DEALER | DISTRIBUTOR or null |
| RETAILER | DEALER, DISTRIBUTOR, or null |
| CUSTOMER | RETAILER, DEALER, DISTRIBUTOR, or null |
| DISTRIBUTOR | null only |

Reject: CUSTOMER as parent; cross-vendor parents; cycles.

## Independent / direct customers

`parent_id IS NULL` — includes:

| `acquisition_source` | Use |
|----------------------|-----|
| `ONLINE` | Store registration / checkout |
| `FB_LEAD` | Facebook / social lead |
| `WALK_IN` | Counter |
| `PHONE` | Phone order |
| `REFERRAL` | Referred (optional `acquisition_meta.referrer_id`) |
| `OTHER` | Catch-all / legacy ETL |

`acquisition_meta` JSONB examples: `{ "campaign": "...", "form_id": "...", "utm_source": "facebook" }`.

## Columns (Postgres)

See schema plan. Summary:

- `party_type`, `parent_id` (FK), `acquisition_source`, `acquisition_meta`, `status`
- Indexes: `(vendor_id, party_type)`, `(vendor_id, parent_id)`, `(vendor_id, acquisition_source)`
- Trade pricing: `party_price_rules` (item × party_type × mode/value) — Phase 10

## ETL

| Legacy | New |
|--------|-----|
| `type` | uppercase → `party_type` (default `CUSTOMER`) |
| `ref_from = 0` | `parent_id` null |
| `ref_from > 0` | `parent_id` if valid same-vendor parent else null |
| (none) | `acquisition_source` null or `OTHER` |

## Offers

`offers.customer_type` matches `party_type` when set; `sales_channel` still restricts ecommerce vs counter.

## Portals (Phase 10)

Dealer/Distributor/Retailer login roles + downline order scopes — see [docs/phase-10/README.md](../phase-10/README.md).
Schema `customers.user_id` links login users to parties.
