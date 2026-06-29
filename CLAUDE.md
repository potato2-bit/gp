# CLAUDE.md — Working Memory

## Project Direction (as of 2026-04-24) — PIVOTED

Primary goal: design the autonomous TEC-based PV-cleaning robot, at three scales — commercial, residential, street-lamp PV — for deployment in Egypt's new sustainable cities.

Benban calculations → now only feasibility evidence inside the methodology chapter, proving TEC atmospheric water harvesting works in arid Egyptian climate.

See `memory/project_context.md` for the full pivot brief.

## Chat style
Use `skills/terse-chat` for all conversational replies. File outputs stay full quality.

## Key files
- `REE598_proposal.tex` — current proposal (needs table + numbering fixes, see `docs/REE598_PROPOSAL_REVIEW.md`)
- `memory/project_context.md` — authoritative project direction
- `docs/TWO_WEEK_PROJECT_PLAN.md` — schedule (to be updated to reflect pivot)
- `skills/` — domain skills (mechanical, electrical, renewable-energy, robotics, etc.)
- `exhibition/here.pdf` — the exhibition idea-validation templates (Gmail draft: DVF / Empathy / Problem / Impact)
- `exhibition/idea_validation_results.{tex,pdf}` + `IDEA_VALIDATION_RESULTS.md` — those 4 frameworks filled in for this project (built 2026-06-17)

## Skills added 2026-06-17
- `idea-validation` — apply DVF / Empathy / Problem-Statement / Impact-Statement (and value-prop / lean-canvas) frameworks to the project; output filled LaTeX/PDF + Markdown. (also in global `~/.claude/skills/`)
- `framework-extraction` — pull a template/diagram out of a photo or PDF (PyMuPDF) and reproduce it filled-in.

## Conventions
- LaTeX: chapter-based numbering, IEEE citations, SI units
- Python: numpy/scipy/pandas/matplotlib; LaTeX-compatible figure output
- All technical claims cited (IEEE format)

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
