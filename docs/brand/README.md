# Oyeva Sales: brand

Files in this folder: the logo set (SVG with outlined text, PNG exports), `tokens.json` (the
source of the tokens) and `tokens.css` (CSS custom properties generated from it). The frontend
copies what it needs into `frontend/`; nothing here is edited by the frontend.

Oyeva Sales is an AI sales analyst for retailers. People upload a sales file and, if they have
one, a document about their business; they ask questions in plain English; every number comes
from code and every explanation shows where it comes from. The identity says the same thing:
**black for focus, metal for precision, violet for what we stand behind.**

## Voice

- Plain English. A shop owner, not a financial analyst, should understand every sentence. A
  technical word is explained the first time or replaced.
- Numbers come with their origin. Never "sales grew strongly": "sales grew 5.06% (Certified,
  Jan to Aug 2026 vs 2025)".
- Say what is missing. "Your document doesn't cover this." is a complete, honest answer.
- No hype, no exclamation marks, no emojis.
- Interface copy is short and in sentence case: "Use sample data", "How was this calculated".

## Visual foundations

**Black** is the ground. The page is `ink-950`, content sits on `ink-850` cards separated by
`ink-700` hairlines. Surfaces get lighter as they come forward (`ink-950` page, `ink-900` rail,
`ink-850` cards, `ink-800` inputs and popovers). Cards use borders, not shadows; only floating
things (popovers, drawers) take `shadow-raised`.

**Metal** is the structure and the text. The `metal-*` scale is a cool steel grey: `metal-100`
for text and numbers, `metal-300` for secondary text, `metal-400` for muted text, `metal-500` for
the borders of controls. The polished chrome gradient is reserved for the logo and, at most, one
hero element per screen (the upload screen title):

```css
/* Chrome: logo and one hero element only */
background: linear-gradient(135deg, #F6F7FA 0%, #C2C5CF 28%, #7A7E8B 50%, #D8DAE2 70%, #8C909D 100%);
-webkit-background-clip: text; background-clip: text; color: transparent;
```

**Violet** is the action and the commitment. `violet-600` fills primary buttons and the
**Certified** label: violet means "computed by a tested function, we stand behind this number".
`violet-300` is for links and active navigation. Use violet sparingly: if everything is violet,
nothing is certified.

Signals: `teal-400` is the market (Statistics Canada), `amber-400` is the user's own documents and
the warnings of the upload checks, `green-400` and `red-400` are check results. A signal color
always comes with a word; color is never the only carrier of meaning.

Type: **Sora** (display, headings, big numbers) gives the geometric, engineered feel of the
wordmark; **Inter** carries the interface and the answers; **JetBrains Mono** shows code and metric
names. Numbers use tabular figures (`font-variant-numeric: tabular-nums`). All three load from
Google Fonts.

Shape: radii from `radius-sm` (labels) to `radius-lg` (cards); pills (`radius-full`) only for
status and citation chips. Spacing on a 4 px grid (`space-1` to `space-12`). Controls are at least
36 px tall, 44 px for primary actions.

## The five provenance labels

The heart of the interface. Every chart, table and explanation carries one label, its name always
written out.

| Label | Value in the API | Style | Tooltip |
|---|---|---|---|
| Certified | `certified` | `violet-600` fill, white text | Computed by a tested function with a fixed definition. |
| Exploratory | `exploratory` | dashed `violet-400` outline, `violet-300` text | Computed by code the assistant wrote for this question. Review the code. |
| Market | `market` | `teal-400` outline and text | Official statistics (Statistics Canada), fetched by code. |
| Your documents | `documents` | `amber-400` outline and text | From the document you uploaded. Not a calculation. |
| Context | `context` | `metal-400` outline and text | From the web. Not computed from your data. |

Document references in text (`[D6]`) are `amber-400` pills; web references (`[W1]`) are
`metal-400` pills.

## Charts

- Ground `ink-850`, grid lines `ink-700`, axis labels `metal-400` in `small`.
- Series order: `violet-400` (the business), `teal-400` (the market benchmark), `amber-400`,
  `metal-300`. A dashed line (`style: dashed`) marks a trend or a target, never a different
  source.
- Money: `$` with thousands separators (en-CA), `1.2M` above a million on axes.
- Each chart card shows its provenance label top left and a "How was this calculated" button.

## Iconography

Line icons, 1.75 px stroke, round caps and joins, on a 24 px grid (the Lucide set fits). Icons are
`metal-300`, or `currentColor` inside buttons. No filled or two-tone icons, no emojis.

## Logo

The mark is a chrome ring, the O of Oyeva, opened at the top right where a violet trend line
breaks out of it: the business measured against its market, and going past it. The wordmark sets
**Oyeva** in Sora SemiBold with the chrome finish and **Sales** in Sora Light, `violet-300`.

| File | Use |
|---|---|
| `oyeva-logo.svg` | Primary lockup, on black and dark surfaces |
| `oyeva-logo-light.svg` | On white and light surfaces (graphite instead of chrome, `violet-700`) |
| `oyeva-logo-white.svg`, `oyeva-logo-black.svg` | One color, when gradients cannot be printed or embroidered |
| `oyeva-mark.svg` and its `-light`, `-white`, `-black` versions | The mark alone: app header, avatars |
| `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` | Browser tab and home screen: the mark on a black tile, heavier strokes |
| `social-preview.png` | GitHub social preview and link cards (1280 x 640) |

Rules:

- Clear space around the logo: at least the width of the ring stroke times two on every side.
- Minimum size: lockup 120 px wide on screen, mark 20 px (below that, use the favicon).
- Never recolor the mark, never put the chrome version on a light background, never stretch,
  outline, shadow or rotate it, never set "Oyeva Sales" in another font next to the mark.

## Accessibility

- Text contrast at least 4.5:1 on its surface (all text tokens are checked against `ink-850` and
  `ink-800` in their usage notes); 3:1 for control borders, focus rings and icons.
- Every interactive element shows `shadow-focus` on keyboard focus.
- Meaning never rests on color alone: labels are written, statuses have words.

## Not this brand

- No blue-to-purple gradients, glows or neon. The only gradient is the chrome of the logo.
- No colored left borders on cards, no emoji cards, no illustrations of people.
- Never the name, logo, colors or initials of another company, including the companies whose data
  or whose founders inspired a demo.
