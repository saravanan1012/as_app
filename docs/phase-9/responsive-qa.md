# Responsive QA checklist

Manual pass at **375**, **768**, and **1280** widths (browser DevTools). Mark when verified.

## Public / Store

| Screen | 375 | 768 | 1280 | Notes |
|--------|-----|-----|------|-------|
| `/` landing hero (brand dominant, one CTA) | ☐ | ☐ | ☐ | No card clutter in hero |
| `/products` list | ☐ | ☐ | ☐ | |
| `/products/:id` | ☐ | ☐ | ☐ | Add-to-cart only if Store on |
| `/login` | ☐ | ☐ | ☐ | |
| `/store` catalog | ☐ | ☐ | ☐ | |
| `/store/cart` | ☐ | ☐ | ☐ | |
| `/store/checkout` | ☐ | ☐ | ☐ | COD + mock Razorpay |
| `/store/orders` | ☐ | ☐ | ☐ | |
| `/store/register` | ☐ | ☐ | ☐ | |

## Platform (SUPER_ADMIN)

| Screen | 375 | 768 | 1280 |
|--------|-----|-----|------|
| `/platform` vendors + Store switch | ☐ | ☐ | ☐ |
| `/platform/vendors/new` | ☐ | ☐ | ☐ |
| `/platform/vendors/:id` | ☐ | ☐ | ☐ |

## Admin (vendor)

| Screen | 375 | 768 | 1280 | Notes |
|--------|-----|-----|------|-------|
| Nav / drawer usable | ☐ | ☐ | ☐ | RBAC-filtered |
| `/admin` dashboard | ☐ | ☐ | ☐ | |
| Sales list + detail + invoice PDF | ☐ | ☐ | ☐ | Table → stacked on mobile |
| Purchase + GRN | ☐ | ☐ | ☐ | |
| Items / Stock | ☐ | ☐ | ☐ | |
| Customers hierarchy | ☐ | ☐ | ☐ | Filters usable on phone |
| Suppliers / Offers / Tx / Users / Audit | ☐ | ☐ | ☐ | |

## Smoke script (after UI pass)

1. Enable Store → register customer → buy `DEMO-NEEM` COD → see order.  
2. Admin: confirm SO + stock drop.  
3. Staff login: no Users / Platform.  
4. Superadmin: Open admin for vendor-two → items do not include `DEMO-*`.
