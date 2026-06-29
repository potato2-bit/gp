---
name: exhibition-poster
description: >
  Use this skill to design and perfect an exhibition POSTER and the matching PITCH
  DECK / presentation for an innovation competition or expo — and to do it in Rahma's
  humanized, creative, engaging voice. Trigger whenever the user mentions a "poster",
  "exhibition poster", "expo", "demo day", "innovation prize/award", the "Special
  Innovation Award", "innovation for impact", "pitch deck", "presentation slides", or
  asks to "make this poster perfect", "fill in the slides", "make it win", or "make it
  more engaging / creative / humanized". Produces a finished A1 poster (.pptx) and a
  filled judged-against-the-rubric deck (.pptx), built from the project's real numbers,
  scored against the competition rubric, and written so a non-specialist instantly gets
  it. Pairs with idea-validation (content), framework-extraction (read a template from a
  PDF/photo), humanizer (voice), and the pptx skill (file mechanics).
---

# Exhibition Poster & Pitch Skill

## Purpose

Turn a blank poster and an empty slide skeleton into competition-winning artifacts: an
A1 exhibition **poster** that stops a judge walking past, and a **pitch deck** that maps
cleanly onto the award rubric. Both carry the project's real numbers and are written in
Rahma's voice — plain, warm, confident, and concrete. The output is not a lecture on
"how to make a good poster"; it is *this* poster and *this* deck, finished.

This skill wins on three things judges reward: a problem they feel in one sentence, an
innovation they can repeat back ("it makes its own water"), and impact with numbers on it.

## When to use

- "Make this poster perfect for the exhibition / for the innovation prize."
- "Fill in the innovation-for-impact slides" / "build the pitch deck."
- "Make the presentation more creative / engaging / humanized / Rahma-style."
- Any judged expo, demo day, or pitch panel where a poster and/or deck is the deliverable.

Pair it: run `idea-validation` first if the problem/impact framing isn't settled; use
`framework-extraction` to read a template out of a PDF or photo; always finish through the
voice rules in `references/rahma_voice.md` (the humanizer mandate).

## The two deliverables

1. **A0 poster** (841 × 1189 mm, 33.11 × 46.81 in, portrait) — read at three distances:
   the *title + hook* from across the hall, the *big impact numbers* from a few steps away,
   the *detail* up close. Built with `scripts/build_poster.py` (it lays the design out at A1
   then scales the whole slide to A0, so the output is **always A0**).
2. **Pitch deck** (16:9, the 10-section "innovation for impact" structure) — one idea per
   slide, a headline that states the takeaway, minimal text. Built with `scripts/build_deck.py`.

There is also a print-ready **LaTeX A0 poster** variant at `exhibition/POSTER_A0.tex`
(tcolorbox + tikz, same palette/zones as the pptx; compiles with `pdflatex`, needs
`hero.png`/`proof.png` beside it). Use it when the exhibition wants A0 and a vector PDF.
Gotcha: center long lines in a tcolorbox with explicit `\centering ... \par`, never bare
`halign=center` on a single line, or the word-spacing collapses.

## Workflow

1. **Gather real content — never invent.** Pull every fact and number from the project's
   own files. The canonical source map and the current numbers live in
   `references/project_facts.md`. If a figure isn't there, mark it `[confirm]` rather than
   guessing.
2. **Score against the rubric.** Open `references/award_rubric.md` — the Special Innovation
   Award asks nine specific questions (problem, user, evidence, solution, value, impact,
   demo readiness, business model). Every one must have a clear answer somewhere on the
   poster and in the deck. Treat the rubric as the judge's checklist, because it is.
3. **Write in Rahma's voice.** Apply `references/rahma_voice.md`: plain language a
   non-specialist gets, one strong claim per line, numbers attached, no AI filler. This is
   the humanizer pass — do it before anything ships.
4. **Lay it out with the design system.** Use `references/design_system.md` for the palette,
   type scale, poster grid, and the deck's headline-per-slide rule.
5. **Build the files.** Run the two scripts (they read the source templates and write
   finished copies — they don't overwrite the originals). Edit content in
   `references/project_facts.md` or the `CONTENT` block at the top of each script, never by
   hand-positioning shapes.
6. **Render and inspect.** If LibreOffice (`soffice`) is available, export the poster to PNG
   and actually look at it; fix overflow, contrast, and balance. Iterate until it reads at
   all three distances.
7. **Run the pre-flight checklist** (below) and hand over the files plus a one-line "why
   this wins" note.

## What makes it win (and what loses)

**Win:**
- A title that says what it *is*, plus a hook that says why it's clever. ("Autonomous
  Self-Watering PV-Cleaning Robot" + "The cleaner that makes its own water.")
- 3–5 huge numbers, each with a unit and a basis. Numbers are the poster's loudest voice.
- One clean system diagram (air → cooler → water → clean panel) beats three paragraphs.
- The "what's new" stated as a contrast: what everyone else does, then the one thing you do
  differently.
- Demo readiness and a business/adoption path — judges score "real-world impact," not just
  cleverness.

**Lose:**
- A wall of paragraphs. If a judge has to read to understand, the poster already failed.
- Vague impact ("significant benefits", "various stakeholders"). Name the user, attach the number.
- Stock-template colors and clip-art. Use the project's own identity (solar + water + Egypt).
- A deck that repeats the poster. The deck is the spoken story; the poster is the silent one.

## Output format

- `exhibition/POSTER_perfected.pptx` — the finished A1 poster.
- `exhibition/innovation_for_impact_filled.pptx` — the finished deck.
- Optional `exhibition/POSTER_perfected.png` — render for quick review / printing proof.
- Keep the source files in `Downloads/` untouched; write perfected copies into `exhibition/`.

## Pre-flight checklist

- [ ] Title readable from ~3 m; hook line present and memorable.
- [ ] Every rubric question (problem, user, evidence, solution, value, impact, demo, model)
      is answered on the poster and in the deck.
- [ ] 3–5 big stat callouts, each with unit + basis; every number traces to a project file
      or is marked `[confirm]`.
- [ ] One system/flow diagram; no paragraph longer than ~3 lines.
- [ ] "What's new" framed as a contrast against existing solutions.
- [ ] Demo plan + backup, and an adoption/business path, both present.
- [ ] Voice passed through `rahma_voice.md` — no AI-isms, no rule-of-three padding, no vague
      attributions.
- [ ] Author, course, supervisor, and contact/QR on the poster footer.
- [ ] Palette and type consistent across poster and deck.

## Invariants

- Finish the artifacts; don't describe how to make them.
- Every number comes from the project's files; flag the rest as `[confirm]`.
- Plain language over jargon — the rubric explicitly rewards a non-specialist understanding it.
- Don't clobber the source templates; write perfected copies.
