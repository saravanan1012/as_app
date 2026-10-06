# Phase 4 — Transactional core (COMPLETE)

PO / SO / GRN / stock ledger / GST / returns / adjustments.

## Migration

`20261005_0003` — purchase_orders (+ details), goods_receipts (+ lines), purchase_returns (+ details), sale_orders (+ details with CGST/SGST/IGST), sale_returns (+ details), order_status_events, stock_adjustments (+ lines). (`transactions` ref index was added in Phase 3.)

## GST rules

| Context | Pricing | Split |
|---------|---------|-------|
| Purchase | Exclusive (cost + GST) | Line `gst_amount` only |
| Sales | Inclusive when `item.sale_price_includes_gst` | CGST+SGST if vendor `state_code` == shipping state; else IGST |

Helpers: `app/core/gst.py`.

## Stock ledger

`app/services/stock_ledger.py` — `SELECT … FOR UPDATE`, writes `stock_movements` with reasons:

`PO_RECEIVE`, `PO_RETURN`, `SO_SALE`, `SO_RETURN`, `SO_CANCEL`, `ADJUSTMENT` (+ transfer reasons reserved).

**PO create does not add stock.** Only GRN receive does.

## APIs

| Resource | Paths | Permission |
|----------|-------|------------|
| Purchase orders | `GET/POST /api/purchase-orders`, `GET …/{id}` | `purchase.orders.*` |
| GRN receive | `POST /api/purchase-orders/{id}/receive` | `purchase.orders.write` |
| Goods receipts | `GET /api/goods-receipts` | `purchase.orders.read` |
| Purchase returns | `POST /api/purchase-returns` | `purchase.orders.write` |
| Sale orders | `GET/POST /api/sale-orders`, `GET …/{id}` | `sales.orders.*` |
| Confirm / cancel | `POST …/{id}/confirm`, `POST …/{id}/cancel` | `sales.orders.write` |
| Status events | `GET /api/sale-orders/{id}/events` | `sales.orders.read` |
| Sale returns | `POST /api/sale-returns` | `sales.orders.write` |
| Stock movements | `GET /api/stock-movements` | `stock.read` |
| Adjustments | `POST /api/stock-adjustments` | `stock.write` |

### Statuses

- **PO:** `DRAFT`, `ORDERED`, `PARTIAL_RECEIVED`, `RECEIVED`, `CANCELLED`, `RETURNED`
- **SO:** `DRAFT`, `CONFIRMED`, `CANCELLED`, `RETURNED` (payment / fulfillment separate)

`CONFIRMED` SO deducts stock; cancel of confirmed restores (`SO_CANCEL`). Draft confirm deducts.

## Verify

```bash
docker compose up -d --build
docker compose exec api pytest -q
# or local pytest against migrated DB
```

## Next

**Phase 5** — Ecommerce / Store APIs — see `../phase-5/README.md`.
