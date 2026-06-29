# Figures for the report

Project: **Atmospheric Water Harvesting for Autonomous PV Panels Cleaning**.

Place exported assets here so `main_report.tex` can include them.

| File | Source | Required? |
|------|--------|-----------|
| `pvsyst_loss_diagram.pdf` | PVsyst simulation report (loss diagram export). See [docs/PVsyst_runbook.md](../docs/PVsyst_runbook.md). | Recommended |
| `pvsyst_loss_diagram.png` | Alternative if PDF not available; update `\includegraphics` in `main_report.tex`. | Optional |

Optional (from Python / Excel):

- Monthly RH or humidity-ratio plot from `output/psychrometrics_monthly.csv` after running `scripts/fetch_nasa_power.py` and `scripts/psychrometrics_hourly.py`.
