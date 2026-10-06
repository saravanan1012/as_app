# Phase 10 — B2B Trade Portal (COMPLETE)

Distributor / Dealer / Retailer portals, per-product trade pricing, qty-tier delivery charges, and shipment tracking (AKR Parcel / Maruthi Parcel).

## Hierarchy

`DISTRIBUTOR → DEALER → RETAILER → CUSTOMER` (any level may also be independent except Distributor).

## Pricing (2B)

- Admin sets `party_price_rules` per item × party type: `PERCENT_OFF` | `FIXED_OFF` | `FIXED_PRICE`
- Trade party sets **sell price** on B2B order (≥ trade cost); end customer pays sell price
- Ecommerce / direct CUSTOMER always pays MSRP (`sale_price`)
- Online flag: Store shows `is_online_sale` only; B2B catalog includes offline SKUs

## Delivery charge

Vendor `settings.shipping.qty_tiers` by total bag/units; fallback `flat_rate` / `free_over`.

## Tracking

Staff: `PATCH /api/sale-orders/{id}/shipment` with `courier` (`AKR_PARCEL` | `MARUTHI_PARCEL`) + `tracking_number`.

All party logins see status + courier + tracking + invoice PDF (B2B `/b2b/orders`, Store `/store/orders`).

## Demo logins (password `User@123`)

### Staff

| Email | Role | Home |
|-------|------|------|
| `superadmin@as.com` | SUPER_ADMIN | `/platform` |
| `admin@as.com` | ADMIN | `/admin` |
| `manager@as.com` | MANAGER | `/admin` |
| `staff@as.com` | STAFF | `/admin` |

### Trade hierarchy (`as-demo`)

```text
Chennai Distributor (distributor@as.com)
├── Anna Nagar Dealer (dealer@as.com)
│   ├── Pondy Bazaar Retailer (retailer@as.com)
│   │   ├── Priya End Customer (retail-customer@as.com)
│   │   └── Karthik End Customer (customer2@as.com)
│   └── Adyar Retailer (retailer2@as.com)
│       └── Meena End Customer (customer3@as.com)
└── T Nagar Dealer (dealer2@as.com)
Coimbatore Distributor (distributor2@as.com)
└── Coimbatore Dealer (dealer3@as.com)
    └── RS Puram Retailer (retailer3@as.com)
Walk-in Direct Customer (direct@as.com)   ← independent, no parent
```

| Email | Role | Notes |
|-------|------|-------|
| `distributor@as.com` | DISTRIBUTOR | Primary tree; sample SO to dealer |
| `distributor2@as.com` | DISTRIBUTOR | Second region |
| `dealer@as.com` | DEALER | Under Chennai dist; SO to retailer |
| `dealer2@as.com` / `dealer3@as.com` | DEALER | Extra downline |
| `retailer@as.com` | RETAILER | Orders for end customers + tracking |
| `retailer2@as.com` / `retailer3@as.com` | RETAILER | Extra downline |
| `retail-customer@as.com` | CUSTOMER | Seed order `SO-DEMO-TRACK-1` (AKR) |
| `customer2@as.com` / `customer3@as.com` | CUSTOMER | Extra end buyers |
| `direct@as.com` | CUSTOMER | Independent / walk-in |

### Sample data seeded

- Trade price rules on all `DEMO-*` SKUs: Distributor 30% / Dealer 20% / Retailer 10% off MSRP
- Offline B2B SKU: `DEMO-BULK-NEEM` (`is_online_sale=false`)
- Qty-tier shipping: ≤2 → ₹80, ≤9 → ₹40, ≥10 free
- Orders: `SO-DEMO-TRACK-1` (AKR), `SO-DEMO-TRACK-2` (AKR), `SO-DEMO-DEALER-1` (Maruthi), `SO-DEMO-DIST-1` (unfulfilled), `SO-DEMO-DIRECT-1`

## APIs

- `/api/b2b/*` — me, downline, catalog, cart preview, orders
- `/api/party-price-rules` — admin trade prices
- `/api/vendor-settings/shipping` — qty tiers + couriers
- `/api/store/my-orders` — customer orders incl. tracking

## Verify

```bash
docker compose exec -T api alembic upgrade head
docker compose exec -T api python -c "from app.db import SessionLocal; from app.seed import run_seed; db=SessionLocal(); run_seed(db); db.close()"
docker compose exec -T api pytest -q tests/test_phase10_b2b.py
```
