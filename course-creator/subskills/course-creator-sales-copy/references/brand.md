# Brand Profile (`brand.md`)

Brand identity is **data the requester owns**, not instructions. It lives in
`brand.md` at the project root (or the course root). Every brand-aware output
inherits from it.

Inheritance chain: **`brand.md` → per-video `style.md` → output.**
`style.md` copies resolved values and states **only the deltas**.

## Find it first

1. `brand.md` in the working directory, then walk up to the project root.
2. Found → inherit. Do not re-ask what it already answers.
3. Absent → run the interview below and write the file.

## Interview order

Ask exactly this, in this order, batching where possible:

1. **Product name** — what is being sold or taught.
2. **Website URL** *(optional)*.
3. **Brand name** — the company or creator identity behind it (may equal the product name).
4. Then resolve colour and fonts:
   - URL supplied → **extract** from the website (see below).
   - no URL → ask for a **local project path** → extract from the project.
   - neither → **ask manually**.
5. **Vertical** — infer from the gathered material; ask only if ambiguous (see Verticals below).

Colour and fonts are *derived*, not asked, whenever a source exists.

## Extraction tier 1 — website URL

| Look for | Yields |
|---|---|
| `<title>`, `og:site_name`, `og:title`, `meta description` | name · tagline |
| `meta[name=theme-color]`, `:root { --color-* }`, Tailwind `theme.extend.colors` | palette roles |
| `font-family` declarations, Google-Fonts `<link>`, `--font-*` | display / body / caption fonts |
| `<img>` with "logo" in `src`/`alt`, `og:image`, favicon | logo files |
| visible headings and CTA button text | tone words · CTA verb |

Fetch the page, record the resolved values, and mark each
`source: extracted-from <url>`. If the site and the screenshots disagree, use the
most direct current evidence and flag the conflict.

## Extraction tier 2 — local project path

Run `scripts/extract_brand.py <path>`. It reads only design surfaces and **never
reads `.env` or any secret file**:

| Source | Yields |
|---|---|
| `tailwind.config.{js,ts}` → `colors`, `fontFamily` | palette · fonts |
| `**/globals.css` `:root { --color-*, --font-* }` | palette · fonts |
| `tokens.json`, `theme.*`, `stitches.config.*` | palette · fonts |
| `package.json` `name` | name |
| `README.md` first heading | name · tagline |
| `public/`, `assets/` for logo-like files | logo files |

Mark each `source: extracted-from <path>`.

## Extraction tier 3 — manual

Batched options block, one recommended pick each:

```
1. Tone — measured (recommended) / patient / playful / authoritative
2. Background — #0B0B0F dark (recommended) / #FAFAF8 light
3. Accent — #4F7CFF / #12B981 / #F97316 / hex of your choice
4. Display font — Inter / Space Grotesk / Playfair Display
5. Body font — Inter (recommended) / Source Sans 3 / IBM Plex Sans
```

## Schema

```markdown
# Brand: {brand name}

## Product
- Product name: {}
- What it is: {}
- One-line promise: {}

## Brand
- Brand name: {}
- Tagline: {}
- URL: {}
- Contact: {}

## Vertical
- {saas | devtools | education | ecommerce | fintech | creator | health | food | agency | nonprofit}

## Logo
- Full lockup: {}
- Mark only: {}
- Mono light / mono dark: {}
- Clear space: {}
- Minimum size: {}

## Palette
| Role | Hex | Use |
|---|---|---|
| Background | | |
| Surface | | |
| Text primary | | |
| Text secondary | | |
| Accent | | |
| Accent alt | | |
| Positive | | |
| Negative | | |

## Typography
| Role | Family | Weight | Size |
|---|---|---|---|
| Display | | | |
| Body | | | |
| Caption | | | |
| Mono | | | |

## Voice and tone
- Tone words: {}
- Person: {we | I | the brand}
- Reading level: {}
- Words we use: []
- Words we never use: []
- Preferred TTS voice: {}

## Imagery
- Style: {photographic | illustrated | ui-only | mixed}
- Icon rules: {}
- Illustration rules: {}

## Claims
- Evidence required before a claim: {}
- Never claim: []
- Competitor references: {allowed | avoid}

## Accessibility
- Minimum contrast: {}
- Caption style: {}
- Reduced motion: {}

## Provenance
| Field | Source |
|---|---|
| palette | extracted-from https://… |
| display font | user-supplied |
| tone | default |
```

## Verticals

| Vertical | Inference cues | Prompt flavour |
|---|---|---|
| `saas` | pricing page, "sign up", dashboard screenshots | outcome + workflow |
| `devtools` | docs, CLI, GitHub, API | technical precision |
| `education` | syllabus, lessons, instructor | learner journey |
| `ecommerce` | product pages, cart, catalogue | product + offer |
| `fintech` | balances, compliance, security | trust + clarity |
| `creator` | personal name, newsletter, social | personality |
| `health` | clinical terms, wellbeing | calm + evidence |
| `food` | menu, recipes, hospitality | sensory + appetite |
| `agency` | services, case studies, portfolio | proof + craft |
| `nonprofit` | donate, impact, mission | mission + outcome |

Pick one. If two fit equally, ask.
