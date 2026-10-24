# Design fields and CSS variables

ID: `frontend.design`
Category: `design`

Themeable design values exposed as CSS variables and editable from the Design panel.

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `var(--token-name, fallback)`

## Details

Every CSS variable used in generated app code should have a matching design field.

Use `var(--name, fallback)` for colors, fonts, spacing, radii, shadows, and other design tokens. Create matching design fields immediately after writing code that references the variable.

When changing an existing theme, color, radius, font, spacing, or shadow, update the existing Design field value. Do not only patch the fallback in `var(--token, fallback)`: if Hangar injects `--token` from the Design tab, that actual value overrides the fallback.
## Quick examples

- `.card { background: var(--card-bg, #ffffff); border-radius: var(--radius-card, 8px); }`
