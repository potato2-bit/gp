# Design system — solar + water + Egypt

One visual identity across the poster and the deck. It reads as the project: sun (solar/desert
gold), water (the AWH idea), and a clean engineered navy. No stock template, no clip-art.

## Palette (hex)

| Role | Hex | Use |
|---|---|---|
| Navy (primary) | `#0B2A4A` | Header band, footer, headlines, diagram outlines |
| Solar gold (accent) | `#F4A300` | Hook strip, big stat numbers, energy/sun, key highlights |
| Water teal (secondary) | `#1CA9C9` | Water/AWH elements, secondary accents, links |
| Sky tint (surface) | `#EAF4FA` | Card backgrounds, panel fills behind body text |
| Ink | `#16242E` | Body text on light surfaces |
| Muted | `#5B6B76` | Captions, sources, fine print |
| Paper | `#FFFFFF` | Poster/slide background |
| Leaf (positive) | `#2E9E5B` | "saved / recovered / zero" impact ticks |

Contrast rule: gold and teal are accents, never body text. Body is ink on paper/sky; white on
navy. Never gold text on white (fails contrast) — use gold for fills and big numerals only.

## Type

- **Display / headlines:** a strong sans (Montserrat / Poppins / Segoe UI Semibold). Tight,
  confident.
- **Body:** a readable sans (Source Sans, Inter, or Calibri). Generous line spacing.
- Poster type scale (A1): hero title 90–120 pt · hook 54–66 pt · section headline 34–40 pt ·
  body 22–26 pt · stat numeral 110–150 pt · stat label 22–26 pt · caption 16–18 pt.
- Deck type scale (16:9): slide headline 32–40 pt · body 18–24 pt · big takeaway 54–72 pt ·
  caption 12–14 pt.
- Never below 16 pt on a poster or 18 pt on a slide. If text doesn't fit, cut words, don't shrink.

## Poster grid (A1 portrait, 23.39 × 33.11 in)

Margin 0.85 in. Three-distance design:

1. **Header band (navy, full width, ~3 in):** kicker (course · school) · hero title · one-line
   subtitle · author + supervisor. Right corner reserved for logos.
2. **Hook strip (gold, full width, ~1.1 in):** the memorable one-liner in navy, big.
3. **Two-column body:** left = Problem + Users/evidence; right = Solution + "what's new."
4. **System diagram band (full width):** five stages, air → Peltier cooler → distilled water →
   spray + microfibre roller → clean panel, joined by arrows.
5. **Impact stat band (full width):** 4 big gold numerals on sky cards, each with unit + basis.
6. **Three-scale market block + value proposition.**
7. **Status row:** prototype stage · next validation · why it wins.
8. **Footer (navy, full width):** author · course · supervisor · contact · QR placeholder ·
   award line.

Whitespace is a feature — let the big numbers and the diagram breathe. Align everything to the
margin grid; nothing floats.

## Deck rules

- Keep the existing template theme; restyle only color accents and headlines to match this palette.
- One idea per slide. Title states the takeaway. Body proves it in ≤ ~20 words.
- Put one big number or one simple visual on each "impact" and "solution" slide.
- Consistent footer: project short-name · author · slide number.
- Title slide: project name, the hook, author, course, supervisor, date.

## Stat callout pattern (the poster's loudest element)

A sky-tint rounded card. Huge gold numeral on top. One-line ink label under it. Tiny muted
"basis" line at the bottom (where the number comes from). Four across the impact band:

- **~37,674 m³/yr** — trucked water avoided (200 MW site)
- **~200 L/day** — water the prototype makes from air
- **0** — workers on the roof
- **~14 USD/m³** — cost of the water it makes (LCOW)

Numbers come from `project_facts.md`; anything unconfirmed gets a small `[confirm]` tag, not a
guess.
