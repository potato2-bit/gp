---
name: idea-validation
description: >
  Use this skill to apply startup / idea-validation and innovation frameworks to an
  engineering, graduation, or product project and produce exhibition-ready, filled-in
  results. Trigger whenever the user references "idea validation", an "exhibition" or
  "expo" panel, the Desirability / Feasibility / Viability (DVF) sweet-spot, an Empathy
  map or empathy questions, a "Problem Statement" template ([USERS] needs to [NEEDS]
  because [INSIGHTS]), an "Impact Statement", a value proposition, a lean / business-model
  canvas, or asks to validate, pitch, justify, or stress-test a project idea, or to "fill
  in" innovation-framework templates for a specific project. Produces a polished LaTeX/PDF
  (recreating each framework visually, filled in) plus a Markdown mirror, grounded in the
  project's own facts and numbers.
---

# Idea-Validation Skill

## Purpose

Turn a blank innovation / idea-validation framework into a *completed*, defensible
analysis of a specific project. The output is not a lecture on the frameworks — it is the
frameworks **filled in** for this project, with concrete users, quantified impact, and the
riskiest assumptions named. Designed for graduation-project exhibitions, pitch panels,
proposal "motivation" sections, and design-review gates.

## When to use

- The user shows a template (photo, screenshot, slide, PDF) of a validation framework and
  says "apply this to my project" / "fill this in" / "add the results".
- The user mentions an exhibition, expo, demo day, or pitch and needs the idea articulated.
- A proposal or report needs a rigorous problem statement, impact statement, or
  market/feasibility justification.
- Pair with `framework-extraction` when the template lives inside an image or PDF that must
  be read first.

## The core frameworks

### 1. Desirability / Feasibility / Viability (DVF) — Strategyzer "three risks"
The idea must sit in the **sweet spot** where all three overlap. Each circle is a *risk*:

- **Desirable — "Do they want this?"** Risk: the target market is too small, too few
  customers want the value proposition, or you can't reach / acquire / retain them.
- **Feasible — "Can we do this?"** Risk: you can't build, scale, or access the key
  resources (technology, IP, brand), activities, or partners.
- **Viable — "Should we do this?"** Risk: you can't generate more value/revenue than the
  cost structure (revenue stream vs. cost structure).

Fill each circle with project-specific evidence. State what you already know vs. what must
still be tested. Name the **single riskiest assumption** — that is what to validate next.

### 2. Empathy — understanding the user behind the problem
Answer all six, specifically (no generic "users"):
1. Who experiences this problem?
2. What do they currently do?
3. What is difficult, costly, slow, risky, or frustrating for them?
4. What alternatives do they already use?
5. What would make them adopt your solution?
6. Who benefits, who decides, and who may pay or support adoption?

Separate the three roles: **user** (lives the problem), **decision-maker** (says yes),
**payer** (funds it). They are often different people.

### 3. Problem Statement Definition
Template: **`[USERS — be very specific]` needs to `[NEEDS — a verb]` because
`[surprising INSIGHTS]`.**
- USERS: a named, narrow segment — not "people" or "everyone".
- NEEDS: an action/outcome in verb form, not your solution.
- INSIGHTS: the non-obvious truth that makes the problem worth solving (the "aha").
Write the one-sentence assembled statement, then expand each slot beneath it.

### 4. Impact Statement
A good impact statement answers: **What** impact? **For whom?** **How?** **How measured?**
Formula: *"If implemented, our project can help `[target users/beneficiaries]` achieve
`[specific improvement]` by `[solution mechanism]`, leading to `[measurable impact]`."*
Then pick the relevant **impact indicators** and attach a target number to each:
time saved · cost reduced · accuracy improved · waste reduced · energy saved ·
safety improved · accessibility increased · number of users served ·
process efficiency improved · environmental or health benefit.

### Optional companions (add when asked)
Value Proposition Canvas (jobs/pains/gains ↔ products/pain-relievers/gain-creators);
Lean Canvas; assumption map (impact × certainty) to rank what to test first.

## Workflow

1. **Identify the frameworks.** If they come from an image/PDF, run `framework-extraction`
   first to read the template faithfully (including fine print and the exact formula).
2. **Gather project facts.** Read the repo / memory / proposal for the real numbers:
   the segment, the quantified pain, the solution mechanism, costs, and any measured
   results. Never invent figures — pull them from the project's own files and cite them;
   mark anything assumed.
3. **Fill each framework** for the specific project. Be concrete and quantified.
4. **Name the riskiest assumption** and the cheapest test for it.
5. **Produce the deliverable** (below).
6. **List assumptions to verify** so the user can refine before presenting.

## Output format

- **Primary:** a LaTeX → PDF that *recreates each framework visually, filled in* — TikZ
  for the DVF Venn and the three-box problem-statement diagram, highlighted boxes for the
  impact formula, a clean table of impact indicators with targets. Match the project's
  LaTeX conventions (geometry, xcolor, tikz, booktabs; dark-blue headings).
- **Mirror:** a Markdown version with the same content, easy to paste into an email,
  slide, or doc.
- Use the source slides' palette so the result looks like a completed version of the
  original template (blue USERS, red/orange NEEDS, green INSIGHTS; yellow Feasible/
  Desirable, orange Viable).

## Quality checklist

- [ ] USERS are a named, narrow segment — not "everyone".
- [ ] NEEDS is a verb/outcome, not the solution.
- [ ] Every impact indicator has a number (with units) and a source or "assumed".
- [ ] DVF names the single riskiest assumption and how to test it.
- [ ] Empathy separates user / decision-maker / payer.
- [ ] All quantitative claims trace to a project file or a cited source.
- [ ] The deliverable reads as a *completed template*, not a tutorial.

## Invariants

- Fill the frameworks; don't just describe them.
- Ground every number in the project's data; flag assumptions explicitly.
- Keep the user's voice and the source template's visual language.
