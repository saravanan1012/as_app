# UX / information architecture (mobile-first)

## Shells

| Shell | Routes | Audience |
|-------|--------|----------|
| Public | `/`, `/products`, `/products/[id]`, `/contact`, `/login` | Everyone |
| Store | `/store`, `/store/cart`, `/store/checkout`, `/store/orders`, … | When `store_enabled` |
| Vendor admin | `/admin/**` | Staff with vendor permissions |
| Platform | `/platform/**` | `SUPER_ADMIN` |

Vendor slug: prod subdomain or `/v/[slug]/...` prefix for local/Capacitor.

## Public landing (default)

`/` is **company details** + product highlights as **content** (not cart/checkout).

- Hero: vendor/company name (brand-first), short blurb, CTA (Contact / View products / Store if enabled)
- Product info section or link to `/products`
- No ecommerce cart on landing

`/products/[id]` = normal product detail (specs, images, description). Add-to-cart only if Store enabled (CTA → `/store/...`).

## Store menu

- Super admin enables via vendor settings `features.store_enabled`
- Public header: show **Store** only when enabled → navigates to `/store` (ecommerce catalog, cart, checkout)
- Capacitor WebView uses same routes

## Admin menus (RBAC-filtered)

Typical groups (hide if no permission):

- Dashboard
- Sales Orders
- Purchase Orders
- Stocks / Items / Locations
- Customers (party type filters)
- Suppliers / Offers / Transactions / Users / Audit

## Login redirect

See [rbac-matrix.md](./rbac-matrix.md) — sales- vs purchase-weighted homes.

## Mobile-first rules

- Sticky primary actions; filters in slideover
- Tables → card list below `md`
- Large tap targets; no hover-only controls
- Theme tokens from Matte Gold (see [themes.md](./themes.md))
