# Vendor settings (JSONB)

Stored on `vendors.settings`. Super admin (permission `platform.vendors.manage`) can PATCH any vendor’s settings, including **Store** enable/disable.

## Canonical shape

```json
{
  "branding": {
    "logo_url": "",
    "primary": "#D4AF7C",
    "theme_id": "matte_gold",
    "store_name": "",
    "company_blurb": "",
    "company_tagline": ""
  },
  "features": {
    "store_enabled": false,
    "cod": true,
    "razorpay": true,
    "reviews": true
  },
  "payments": {
    "razorpay_key_id": "",
    "razorpay_key_secret_ref": ""
  },
  "shipping": {
    "flat_rate": 0,
    "free_over": null
  },
  "limits": {
    "max_items": 5000,
    "max_staff": 20
  },
  "tax": {
    "gstin": "",
    "state_code": ""
  },
  "locale": {
    "currency": "INR",
    "timezone": "Asia/Kolkata"
  }
}
```

## Store flag

| `features.store_enabled` | Behavior |
|--------------------------|----------|
| `false` (default for new vendors) | Hide **Store** nav; `/store` → redirect `/`; Store APIs 403/404 |
| `true` | Show Store menu → ecommerce; APIs allowed |

Landing `/` and product **info** pages stay public regardless of Store flag.

## Theme

- Platform default theme_id: `matte_gold` (see [themes.md](./themes.md)).
- `branding.primary` may override accent; full palette switch uses `theme_id` ∈ `matte_gold` \| `rose_gold` \| `deep_gold` \| `vibrant_gold`.

## Secrets

Do not store raw Razorpay secrets in JSON long-term; use `razorpay_key_secret_ref` pointing to env/vault. Staging may use env `RAZORPAY_*` fallbacks per vendor override later.
