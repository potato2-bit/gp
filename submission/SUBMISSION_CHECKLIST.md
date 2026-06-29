# Final submission pack — QA checklist (Days 13–14)

**Official project title:** Atmospheric Water Harvesting for Autonomous PV Panels Cleaning.

Use this before submitting the graduation report to your department.

## Files to include

- [ ] `main_report.pdf` (compiled from `main_report.tex`; run BibTeX if references changed)
- [ ] `proposal_short.pdf` (3-day proposal)
- [ ] `project_inputs.yaml` (single source of truth for numbers)
- [ ] `output/calculation_summary.txt`, `output/lcow_table.csv`, `output/lcow_table_autogen.tex`
- [ ] `output/nasa_power_hourly.csv` (if hourly analysis completed)
- [ ] `output/psychrometrics_monthly.csv` (if generated)
- [ ] PVsyst exports in `submission/pvsyst_exports/` per [docs/PVsyst_runbook.md](../docs/PVsyst_runbook.md)
- [ ] `figures/pvsyst_loss_diagram.pdf` (or accept placeholder in PDF until export)

## Cross-checks

- [ ] Abstract numbers match `project_inputs.yaml` and Chapter 2 equations
- [ ] Same $P_{\mathrm{dc}}$, $w$, $N_{\mathrm{clean}}$, $f_{\mathrm{margin}}$ in proposal, report, and YAML
- [ ] Tariff $\pi$ and CAPEX noted as **illustrative** in text
- [ ] All figures referenced exist or are clearly marked placeholder
- [ ] Bibliography compiles; run: `pdflatex` → `bibtex main_report` → `pdflatex` ×2

## Build commands (project root)

```text
pip install -r requirements.txt
python scripts/project_calculations.py
python scripts/fetch_nasa_power.py
python scripts/psychrometrics_hourly.py
pdflatex proposal_short.tex
pdflatex main_report.tex
bibtex main_report
pdflatex main_report.tex
pdflatex main_report.tex
```

## Advisor / department

- [ ] Format matches faculty template (margins, cover page, Arabic abstract if required — add manually)
