#!/usr/bin/env python3
"""Tier 1 — run the low-fidelity CADET DoE.

Reads the low-fi rows of data/doe_design.csv (fidelity in {lowfi, highfi}; high-fi is the
nested subset, also run here), runs the CADET column (build_column.py) per row, and writes
data/cadet_responses.csv with per-cycle responses:
  m_w_kg            water adsorbed per adsorption half-cycle  (loading swing × gel mass)
  removal_frac      mean inlet-humidity removal over the half-cycle
  Q_reg_J, SEC_kWh_per_kg   lumped energy post-model (energy_postmodel.py)
  dP_Pa             Ergun pressure drop (direct, no surrogate)

Fast: seconds per case.  Use --limit N to run a subset.
See docs/DESIGN_SPEC.md §3, Appendix B §3.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cadet"))
import build_column as bc                      # noqa: E402
from energy_postmodel import ergun_dp, lumped_energy   # noqa: E402

M_WATER = 0.018015
DIAM_M = 0.10                                   # fixed column diameter (not a DoE factor)


def run_row(row, params):
    eps = params["bed"]["porosity"]
    rho_bulk = params["bed"]["rho_bulk_kg_m3"]
    L = float(row["L_bed_mm"]) / 1000.0
    dp = float(row["d_p_mm"]) / 1000.0
    u = float(row["u_face_m_s"])
    T_ads = float(row["T_ads_C"])
    RH = float(row["RH_ads_pct"]) / 100.0
    T_reg = float(row["T_reg_C"])
    t_half = float(row["t_half_h"]) * 3600.0

    run = dict(T_C=T_ads, RH_in=RH, L_bed_m=L, diameter_m=DIAM_M, d_p_m=dp,
               u_face_m_s=u, t_end_s=t_half, ncol=60)
    proc, meta = bc.build_column(params, run)
    t, c_out, solid, _ = bc.run_breakthrough(proc, n_time=400)

    # final mean solid loading -> kg/kg ; uptake from regenerated (q0=0)
    q_cadet_final = float(np.mean(solid[-1, :, 0]))           # mol/m3 solid
    q_kgkg = q_cadet_final * M_WATER * (1.0 - eps) / rho_bulk
    area = np.pi * (DIAM_M / 2.0) ** 2
    V_bed = area * L
    m_gel = rho_bulk * V_bed
    m_w = q_kgkg * m_gel

    removal = float(np.mean(1.0 - np.clip(c_out / meta["c_in"], 0, 1)))

    res = dict(m_w_kg=m_w, m_gel_kg=m_gel, dq_kgkg=q_kgkg, q_avg_kgkg=q_kgkg,
               dT_reg_K=(T_reg - T_ads), u_face_m_s=u, L_bed_m=L, d_p_m=dp,
               eps=eps, t_cycle_s=t_half, area_m2=area)
    en = lumped_energy(res, params)
    return dict(m_w_kg=m_w, removal_frac=removal, q_final_kgkg=q_kgkg,
                Q_reg_J=en["Q_reg_J"], SEC_kWh_per_kg=en["SEC_kWh_per_kg"],
                dP_Pa=en["dP_Pa"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design", default=str(ROOT / "data" / "doe_design.csv"))
    ap.add_argument("--out", default=str(ROOT / "data" / "cadet_responses.csv"))
    ap.add_argument("--config", default=str(ROOT / "awh_sim_config.yaml"))
    ap.add_argument("--limit", type=int, default=0, help="run only first N low-fi rows (0=all)")
    args = ap.parse_args()

    params = bc.load_params(args.config)
    rows = [r for r in csv.DictReader(open(args.design)) if r["fidelity"] in ("lowfi", "highfi")]
    if args.limit:
        rows = rows[: args.limit]

    fac = ["T_ads_C", "RH_ads_pct", "T_reg_C", "u_face_m_s", "L_bed_mm", "d_p_mm", "t_half_h"]
    resp = ["m_w_kg", "removal_frac", "q_final_kgkg", "Q_reg_J", "SEC_kWh_per_kg", "dP_Pa"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    n_ok = n_bad = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", *fac, "fidelity", *resp])
        for r in rows:
            try:
                rr = run_row(r, params)
                w.writerow([r["id"], *[r[k] for k in fac], r["fidelity"], *[f"{rr[k]:.6g}" for k in resp]])
                n_ok += 1
            except Exception as e:  # noqa: BLE001
                n_bad += 1
                print(f"  [skip] {r['id']}: {type(e).__name__}: {str(e)[:70]}")
            if (n_ok + n_bad) % 20 == 0:
                print(f"  ... {n_ok+n_bad}/{len(rows)} done")
    print(f"wrote {out}: {n_ok} ok, {n_bad} skipped")


if __name__ == "__main__":
    main()
