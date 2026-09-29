---
id: sd-form-flow
category: screencast-demo
verticals: [saas, fintech, ecommerce, health]
purpose: demonstrate
duration: 45s
energy: calm
tags: [typing, zoom, sfx]
---
# Form / Typing Flow

## When to use
The proof is data being entered. This is the pattern that needs real zoom and
real SFX.

## Beat structure
| Beat | Time | On screen | Motion | SFX |
|---|---|---|---|---|
| 1 | 0:00–0:06 | Why this form matters | `fade-in` | `ambient` |
| 2 | 0:06–0:14 | Full screen so the layout is clear | `fade-in` | `shutter` |
| 3 | 0:14–0:28 | **Zoom to field 1** — characters appear | `zoom` in, `typewriter` | `typing` |
| 4 | 0:28–0:36 | **Zoom to field 2 / a toggle or select** | `zoom` pan | `click` |
| 5 | 0:36–0:41 | Submit — state change visible | `focus-ring` on the button | `click` → `success` |
| 6 | 0:41–0:45 | Ending per §4 | settle | `success` |

## Copy skeleton
`{Why this form.}` / `{Field 1 label and what to enter.}` / `{Field 2.}` / `{What success looks like.}` / `{CTA.}`

## Objects used
`form-field` `input-field` `toggle` `zoom` `typewriter` `pointer-cursor` `success` badge

## Variants
- **Always zoom in on typing and form filling.** Keep the cursor visible and the
  label legible at the zoomed size.
- Blurred sensitive data before production; never invent a filled value that
  supports an unsupported claim.
