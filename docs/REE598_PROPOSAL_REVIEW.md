# REE 598 Proposal — Engineering Review

**Reviewers applied:** Mechanical Engineering · Electrical Engineering · Renewable Energy Engineering
**Source file:** `REE598_proposal.tex` (Apr 23 2026)
**Scope:** numbering, table integrity, internal consistency of numerical claims, thermodynamic/power-budget sanity, and alignment with the pivoted project direction (autonomous TEC cleaning robot for commercial / residential / street-lamp PV in Egyptian new cities).

---

## 1. Structural Issues Fixed

### 1.1 Duplicate section numbering
Every `\section{…}` and `\subsection{…}` command manually embedded the number in the title (e.g. `\section{1.1 Importance of the Project Field}`). Because the document class auto-numbers sections and `\setcounter{secnumdepth}{3}` is set, the output printed the number twice — e.g. **"1.1 1.1 Importance of the Project Field"**. This is what the user observed as "subsubsection numbering repeated" (it was in fact happening at every section and subsection, producing the visual pattern of duplicated triple-level indices).

**Resolution:** Stripped the manual numeric prefixes from all 52 section/subsection headings by regular-expression substitution. LaTeX's auto-numbering now produces a single, correct index (e.g. §1.1, §1.2.1, §6.7.2). Chapter numbering, TOC entries, and cross-references are unaffected because they already used the LaTeX counters.

### 1.2 Header-height fancyhdr warning
Added `\setlength{\headheight}{14pt}` to remove the dozens of fancyhdr underfull warnings caused by the 12 pt font overflowing the default 12 pt `\headheight`.

---

## 2. Table Issues Fixed

### 2.1 Table 3.1 — Deployment Scale Specifications
Two header rows were stacked (main label + italic sub-label) without a separating rule, so the italic row read as a data row. Added `\cmidrule(lr){2-4}` between the two header rows so the sub-header visually attaches to the scale labels.

### 2.2 Table 6.1 — Annual Energy Recovery
Three defects:
1. The multicolumn spanner "Energy recovered by wet clean" had no `\cmidrule`, so the two sub-columns below it read as disconnected headers. Added `\cmidrule(lr){4-5}`.
2. The footnote was wrapped inside the tabular as a `\multicolumn{6}{l}`. This forced a line break of the table's last row and visually overflowed the body. The footnote was moved *outside* the `tabular` environment using `\vspace{0.25em}` + `\par\footnotesize` so the table ends cleanly at `\bottomrule`.
3. Column alignment inconsistency — numeric columns were centred but the values have variable magnitude (2-digit to 6-digit). Retained `c` alignment for readability but tightened column spacing via explicit number formatting (27.0, 118, 2{,}352) so decimal alignment is visually acceptable.

### 2.3 Appendix C — Scale B BOM
`Qty` and `Unit cost (USD)` columns were typeset as `c` (centred). For a numeric BOM this is wrong — numbers should be right-aligned so unit digits align. Changed column spec from `p{4.5cm}p{4.0cm}cc` to `p{4.5cm}p{4.0cm}rr`.

---

## 3. Numerical-Consistency Flags (Not Auto-Fixed — Require Author Decision)

These were **not** silently edited because they are substantive engineering choices, but they must be reconciled before REE 599 fabrication.

### 3.1 Tables 6.1 vs. 6.2 — Annual Energy Recovery Contradiction
Tables 6.1 and 6.2 give different numbers for the same physical quantity ("annual energy recovered") at each scale:

| Scale | Table 6.1 recovery vs. no clean (kWh) | Table 6.2 "Annual energy recovered" (kWh) | Ratio |
|-------|---------------------------------------|------------------------------------------|-------|
| A | 27 | 95 | 3.5× |
| B | 3,360 | 15,750 | 4.7× |
| C | 67,200 | 315,000 | 4.7× |

Table 6.1 is internally self-consistent — it is computed from a 3.5 % mean soiling loss (half of 0.5 %/day × 14 days) against the annual yield. Table 6.2, by contrast, implies the recovery is ≈94 % of the annual yield, which is physically impossible (no panel loses 94 % of output to soiling).

**Recommendation:** regenerate Table 6.2 "Annual energy recovered" from the same soiling model used in Table 6.1 and the same tariff. For Scale B at the 20 % untreated-soiling reference: 0.20 × 16,800 = 3,360 kWh, × tariff 0.02 USD/kWh = **67 USD/yr**. Payback = 600 / 67 ≈ **9 years** (not 1.9). Equivalent recalculations for A and C should be carried out and the economics table replaced.

### 3.2 TEC Specific Energy Consumption (§6.2.5)
The proposal reports SEC ≈ 0.927 kWh/L for a TEC1-12706 at the design point. Published experimental data for TEC AWGs in arid climates (including `alqaed2023awg` and `shourideh2021tec` cited in the same document) give SEC = 2.8–12 kWh/L. A **~3× to 10× optimism** in the derived SEC is difficult to defend against the cited literature.

The most likely error source is the air-side mass balance in Eq. 6.11: a cold-plate air mass flow of 2.71 × 10⁻³ kg/s (≈ 8.4 m³/h) is high for a 40×40 mm cold plate with a 60 mm fan — typical free-convection + small fan gives 2–4 m³/h. Recommend recomputing with a datasheet-backed fan curve and applying a conservative η_c in the range 0.30–0.60 (not 0.80).

### 3.3 Hot-Side Temperature Assumption (§6.2.3, §6.3)
Eq. 6.14 sizes the heat sink from T_h as if T_h were a free parameter. In practice T_h is set by the heat-sink equation:
\[ T_h = T_\text{amb} + \theta_\text{sa} \cdot Q_h \]
For T_amb = 35 °C, θ_sa = 0.5 K/W, Q_h = 30.5 W → **T_h ≈ 50 °C**, not the implied ~35 °C used in the COP calculation. Re-solving the Peltier loop with T_h = 50 °C gives ΔT = 36 K, lower COP (~0.28), and higher SEC. Resolve the two-equation system (Eq. 6.4–6.7 and 6.14) simultaneously for a self-consistent operating point.

### 3.4 Heat-Sink Performance Claim (§6.3)
"50 × 50 mm extruded aluminium heat sinks with a 60 mm fan achieve θ_sa ≈ 0.5 K/W." This is optimistic by roughly a factor of 2–4. Datasheets for similar-sized extrusions (Wakefield 670-series, Fischer LA-family, Aavid/Boyd 50 mm profiles) give 1.5–3 K/W at 2 m/s forced airflow. To hit 0.5 K/W one typically needs a 100 mm+ heat-sink footprint or a dedicated coldplate with heat pipes. Either upsize the heat sink in the BOM or accept the higher T_h and its COP penalty.

### 3.5 Scale B Battery Sizing vs. BOM
§6.4 computes E_total = 1,935 Wh and specifies C_batt ≥ 2,420 Wh (at 80 % DoD). The BOM (Table C.1) lists a **1,800 Wh LiFePO₄ pack** — undersized by 25 %. Either raise the BOM to a 2.5 kWh pack (cost ≈ 280 USD for a quality 24 V / 100 Ah LFP with BMS) or reduce E_TEC by operating fewer modules simultaneously.

### 3.6 LiFePO₄ Pack Price
BOM price $180 for 1.8 kWh @ 24 V is below market. Current (Apr 2026) retail for a 24 V / 75 Ah LFP pack with integrated BMS is 350–600 USD. Revise BOM total to reflect a realistic 450 USD, pushing Scale B total to ≈ **900 USD** (not 600). This still gives payback ≈ 13 years at the corrected Table 6.2 tariff figure.

### 3.7 Scale C Gantry Rail Feasibility (mechanical)
Scale C cleans a 200 kWp block with a 1,674 L cleaning event. A 1.67-tonne water reservoir on a mobile gantry is structurally demanding and rarely used in commercial O&M practice. Recommend decomposing Scale C into a fleet of ≥ 4 Scale-B-class units running in parallel, each with its own TEC-AWG and battery. This also aligns with the project pivot toward modular, scale-replicable robots rather than a bespoke gantry design.

### 3.8 Condensate Tank Size (Scale B)
BOM lists a 5 L tank. Cleaning-event volume = 82.8 L. Either the tank must be upsized (≈ 100 L HDPE) or the cleaning event must be spread over multiple harvest nights with interim pump-out to a buffer tank. Clarify the intended operational sequence in §3.2.

---

## 4. Alignment with the Pivoted Project Direction (2026-04-24)

The project direction has pivoted: **autonomous robot design is now the primary deliverable**; Benban-scale calculations serve as feasibility evidence. The proposal as written is already close to this framing (the title reads "Autonomous Thermoelectric-Based Atmospheric Water Harvesting Robot…"), but two adjustments are recommended before REE 599:

1. **Rewrite §3.3 "Deployment Scales" to put street-lamp (Scale A) and commercial-rooftop (Scale B) first.** The current ordering treats Scale C (industrial 200 kWp) as the flagship. The pivot targets new-city deployment — street-lamp PV and rooftops — so Scale A and B should be the design drivers, with C shown as an upwards-scalable stretch case.

2. **Add a new §6.5.4 "Prototype Scale Selection"** that explicitly justifies the Scale-B prototype choice on the basis of (i) realistic manufacturing complexity, (ii) alignment with Egyptian new-city commercial deployment, and (iii) testability on a 10-panel rig at Zewail City.

3. **Chapter 2 Literature Review §§ 2.3 and 2.4** already cover TEC in arid climates and autonomous cleaning robots — retain these as the justification chapter.

---

## 5. Summary of Actions Taken

Files modified in place in `C:\Users\rizk\Desktop\GRADUATION PROJECT`:
- `REE598_proposal.tex` — all section/subsection numbering fixed; three table fixes applied; `\headheight` set to 14 pt.
- `REE598_proposal.pdf` — rebuilt (35 pages, clean compile, all warnings gone except four harmless underfull-hbox in narrow `p{}` cells of the BOM).

Files created:
- `memory/project_context.md` — pivot brief (autonomous robot for commercial / residential / street-lamp PV).
- `CLAUDE.md` — working-memory pointer.
- `skills/terse-chat/SKILL.md` + `outputs/terse-chat.skill` — minimalist chat style.
- `figures/system_architecture.svg` — schematic visual of the designed system (see next section).
- This file: `docs/REE598_PROPOSAL_REVIEW.md`.

Backup of the original proposal is at `outputs/REE598_proposal.backup.tex`.

---

## 6. Open Items for the Next Working Session

- Reconcile Tables 6.1 and 6.2 (energy recovery and economics).
- Re-derive the TEC operating point with a coupled Peltier–heat-sink solver; update SEC, COP, and Q_h figures in §6.2–§6.3.
- Upsize Scale B battery (BOM) and revise total cost.
- Rewrite the scale ordering in §3.3 and add §6.5.4.
- Build a preliminary 3D CAD mock-up of the Scale B unit in SolidWorks / Fusion 360 using the block dimensions in the system architecture figure.
