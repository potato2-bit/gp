# PVsyst runbook — Benban case

**Project title:** Atmospheric Water Harvesting for Autonomous PV Panels Cleaning.

Use this checklist so your simulation matches `project_inputs.yaml` and the report text.

## 1. Project setup

1. Open **PVsyst** → New project.
2. **Site**: Create or select a site near **24.45°N, 32.75°E**, elevation ~180 m (refine from Google Earth).
3. **Meteo**: Import a compatible weather file or use PVsyst’s embedded source that best matches Upper Egypt. Prefer a **TMY** with hourly GHI/DHI if available. If you use PVsyst default Egypt/Aswan-style data, **state the exact dataset name** in the report.
4. **Grid**: Grid-connected PV, **loss fraction user-defined** as per utility PPA if required; otherwise default transformer/availability.

## 2. System definition (align with 200 MW DC block)

- **Nominal DC power**: **200 MW** at STC (or your chosen `P_dc_MW` from `project_inputs.yaml`).
- **Module**: Choose a commercial **mono PERC** datasheet (e.g. ~20–22% STC efficiency) so that **η_module** is consistent with **0.215** used in water-area calculations, or adjust `eta_module_stc` in YAML and re-run `scripts/project_calculations.py`.
- **Inverter**: Central or string inverters sized for **AC** limit per your design; document **DC/AC ratio**.
- **Mounting**: Fixed tilt (common) or **single-axis tracker** — pick **one** and keep it for all sensitivity runs.
- **Shading**: **Near shadings** off unless you have a real row-spacing model.

## 3. Soiling (critical)

1. Open **Project design → Array and system losses → Soiling loss**.
2. Enter **monthly soiling loss** [%] or **soiling factor** per PVsyst version. Justify values for **arid Benban** (low rain, dust): e.g. higher in dry months, slightly lower in rare rainy periods.
3. Cite: [PVsyst — Soiling loss](https://www.pvsyst.com/help/project-design/array-and-system-losses/soiling-loss.html) and 1–2 peer-reviewed soiling papers for Egypt/desert.

## 4. Sensitivity (minimum)

- **Base case**: your justified monthly soiling table.
- **Sensitivity 1**: increase worst-month soiling by **+1% absolute** loss on irradiance (or equivalent factor).
- Optional: **-1%** in a wetter month.

## 5. Exports for the report appendix

Save the following into `submission/pvsyst_exports/` (create folder when you run PVsyst):

| File | Description |
|------|--------------|
| `*.pdf` | Main simulation report (annual energy, PR, losses). |
| `*.PAN`, `*.PVC` | Project files if your PVsyst version uses them. |
| Screenshot or vector export | **Loss diagram** (pie or waterfall) → save as `figures/pvsyst_loss_diagram.png` or `.pdf`. |

## 6. What PVsyst does *not* do

- **AWH water production** — use `scripts/project_calculations.py` and optional `scripts/fetch_nasa_power.py` + `psychrometrics_hourly.py`.
- If cross-check is needed, use **NREL SAM** ([sam.nrel.gov](https://sam.nrel.gov)) with the same DC power and loss philosophy.

## 7. After you export

1. Copy the loss figure path into `tex/chapter_pvsyst.tex` (or add `\includegraphics` in `main_report.tex`).
2. Re-run `pdflatex` on `main_report.tex`.
