# Citation Verification — prototype_design_report / references.bib
Date: 2026-06-02 (automated run). Method: WebSearch against DOI / title / author /
journal / volume / year. (web_fetch on Crossref was blocked by URL-provenance;
WebSearch worked.) IEEE Xplore and MDPI records often do not surface in WebSearch,
so for two DOIs the "unverified" label means "could not confirm", not "wrong".

## Verified CORRECT (no change)
- beattie2012waterspots — 10.1016/j.renene.2012.06.007 — Beattie et al.,
  *Renewable Energy* 48:448-452 (2012). DOI/title/authors/vol/pages all match.
- caron (DOI) — 10.1109/JPHOTOV.2012.2216002 — Caron & Littmann, *IEEE J. PV*
  3(1):336-340 (2013). Confirmed (IEEE doc 6656732).
- shourideh2021tec — 10.1016/j.tsep.2018.03.006 — Shourideh et al., *TSEP* 6:14-26
  (2018). Confirmed (ADS 2018TSEP....6...14S). Minor: one co-author is "Al Lami"
  in sources vs "Al Lababidi" in bib — left as-is.
- riffat2003peltier — 10.1016/S1359-4311(03)00012-7 — Riffat & Ma, *Appl. Therm.
  Eng.* 23(8):913-935 (2003). Confirmed.
- zhao2022teccondenser — 10.1016/j.applthermaleng.2014.01.074 — Zhao & Tan, *Appl.
  Therm. Eng.* 66(1-2):15-24 (2014). Confirmed (key says 2022 but entry year is
  correctly 2014).
- costa2021pvrobot — 10.1016/j.rser.2020.110363 — Costa, Diniz & Kazmerski soiling
  review (RSER 137, 2021). DOI consistent; FIRST NAME corrected Sofia -> Suellen.

## CORRECTED in references.bib
1. **eslami2021tec** — was *Thermal Sci. Eng. Progress* 25:101042 (2021),
   DOI 10.1016/j.tsep.2021.101042. WRONG. Real paper: Eslami, Tajeddini, Etaati,
   "Thermal analysis and optimization of a system for water harvesting from humid
   air using thermoelectric coolers", **Energy Conversion and Management 174:417-429
   (2018), DOI 10.1016/j.enconman.2018.08.045** (ScienceDirect pii S019689041830894X).
   Journal/year/volume/pages/DOI/title all fixed.
2. **kazem2023soiling** — was J. Cleaner Production 411:137258 (2023),
   DOI 10.1016/j.jclepro.2023.137258. WRONG year/vol/pages/DOI. Real paper:
   **J. Cleaner Production 276:123187 (2020), DOI 10.1016/j.jclepro.2020.123187**
   (ADS 2020JCPro.27623187K). Title/authors were correct. Key name kept.
   The report's "0.3-0.8 %/day arid soiling" claim is within this review's range — OK.
3. **luo2022tecmodel** — DOI 10.1016/j.enconman.2020.112596 does NOT map to a Luo
   thermoelectric paper; it maps to Yuan et al., "Performance analysis of thermal
   energy storage in distributed energy system..." (EnConMan 208, 2020). Entry
   DISABLED (made inert in the .bib). The TEC max-parameter relations it backed are
   standard and now cite zhao2022teccondenser + riffat2003peltier.
4. **caron** — key renamed caron2013soilingbenban -> **caron2013soiling** (the paper
   is on First Solar plants in CALIFORNIA, not Benban). Title corrected to as-published
   "...on First Solar Modules in California". \cite updated in the report.

## Numeric claims re-cited / flagged in prototype_design_report.tex
- **PSH 5.8 h/day & PR 0.80 (Benban)** — was \cite{ahmed2021egyptsolar}, a generic
  probabilistic solar-farm model with NO Benban PSH/PR. Re-cited to
  \cite{nasa_power,globalsolaratlas} (authoritative site data); PR 0.80 noted as a
  standard utility-scale design value.
- **1.8 L/m^2 (3.6 L) cleaning water per event** — was \cite{beattie2012waterspots};
  that paper is on dust optical losses, not wet-cleaning water use. Recast as a
  "Design assumption" in both the requirements table and the cleaning-logic section.
- **Robot drive resistive-force equation** — \cite{costa2021pvrobot,pan2022robotdesign}
  are a soiling review and a cleaning-interval study, NOT robot-mechanics sources.
  Flagged in-line; equation is standard textbook mechanics (consider a terramechanics
  reference or removing the cite).

## Unverifiable DOIs (not necessarily wrong)
- ahmed2021egyptsolar 10.1109/TEC.2020.2984479 (IEEE) and pan2022robotdesign
  10.3390/su14127529 (MDPI) could not be confirmed via WebSearch because those
  databases don't surface. Both are noted in the .bib; ahmed is no longer the source
  of any site number, and pan's entry is internally consistent.

## Build
Rebuilt cleanly in /tmp scratch (pdflatex -> bibtex -> pdflatex x2, ieeetr style,
local siunitx shim kept). Final: 27 pages, no bibtex errors, no undefined citations.
NOTE: during editing, the Desktop folder truncated tool-writes on BOTH
prototype_design_report.tex and references.bib (~17.5 KB cutoff). Both files were
reconstructed and copied back via bash `cp`. If editing these large files again,
use bash cat/cp, NOT the Write/Edit tools.
