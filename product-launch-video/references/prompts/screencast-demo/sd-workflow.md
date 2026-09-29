---
id: sd-workflow
category: screencast-demo
verticals: [saas, devtools, agency]
purpose: onboard
duration: 60s
energy: calm
tags: [sequence, screens]
---
# Multi-Step Workflow

## When to use
The product's value is a sequence of real states. Each step needs its own real
screen.

## Beat structure
| Beat | Time | On screen | Motion | SFX |
|---|---|---|---|---|
| 1 | 0:00–0:06 | The outcome this workflow produces | `fade-in` | `ambient` |
| 2 | 0:06–0:14 | Step 1 — real screen, `step-indicator` at 1 | `zoom` | `click` |
| 3..n | 12–14s each | Step n — a **distinct** real screen | `zoom` / `wipe` between | `click` |
| last | 0:52–0:60 | Result state + ending | `success` badge | `success` |

## Copy skeleton
`{Outcome.}` / `{Step n — what you do and why.}` / `{Result.}` / `{CTA.}`

## Objects used
`step-indicator` `browser-chrome` `zoom` `wipe` `toast` `success` badge

## Variants
- Use distinct real screenshots or a screen recording per step. A multi-step
  demo faked from one screen invents states.
