# Themes (gold family)

Source palette sheet: “Pixel by Sajeda” gold themes.  
**Default for Phase 1+ UI:** Matte Gold. Others kept for later runtime switch via `vendors.settings.branding.theme_id`.

Machine-readable tokens: [themes.json](./themes.json)

## Default — Matte Gold (`matte_gold`)

SOFT / ELEGANT / TIMELESS

| Token | Hex | Role |
|-------|-----|------|
| `gold-900` | `#B89B6A` | Text, strong accents, headers |
| `gold-700` | `#D4AF7C` | Primary buttons, links, brand accent |
| `gold-500` | `#E6CFA8` | Borders, chips, secondary surfaces |
| `gold-300` | `#F3E4C8` | Cards / elevated panels |
| `gold-100` | `#FAF6E8` | Page background |

Suggested neutrals (not on sheet; pair with matte gold):

| Token | Hex | Role |
|-------|-----|------|
| `ink` | `#2C2416` | Body text |
| `ink-muted` | `#5C5346` | Secondary text |
| `surface` | `#FFFFFF` | Contrast panels on cream bg |
| `danger` | `#B42318` | Errors (non-gold) |
| `success` | `#3F621A` | Success |

## Reserved — switch later

### Rose Gold (`rose_gold`) — romantic / stylish / modern

`#B76E79`, `#D9898F`, `#EFB5B7`, `#F7D7D9`, `#FFF1E9`

### Deep Gold (`deep_gold`) — rich / bold / premium

`#8B6B2F`, `#C9973B`, `#E1B547`, `#F2D78A`, `#FFF4CC`

### Vibrant Gold (`vibrant_gold`) — energetic / modern / impactful

`#D97706`, `#F4B400`, `#FFD700`, `#FFE680`, `#FFF9E6`

## Nuxt UI mapping (Phase 6+)

Map Matte Gold into Nuxt UI / Tailwind CSS variables, e.g.:

```css
:root {
  --ui-primary: #D4AF7C;
  --color-gold-900: #B89B6A;
  --color-gold-700: #D4AF7C;
  --color-gold-500: #E6CFA8;
  --color-gold-300: #F3E4C8;
  --color-gold-100: #FAF6E8;
  --color-bg: #FAF6E8;
  --color-ink: #2C2416;
}
```

Runtime: load `theme_id` from public vendor branding API; swap CSS variable set. Default `matte_gold` if unset.
