#!/usr/bin/env python3
"""Drive the surrogate over the year for each site -> annual water & energy.

Design factors are frozen for the annual sweep (one bed); only the operating point
(T_ads, RH_ads, T_reg) varies per daily cycle from the climate aggregation. Per cycle the
surrogate predicts m_w (water) and Q_reg (regen heat); fan energy is the deterministic
Ergun parasitic. Writes results/annual_<site>.csv and a cross-site summary used by LCOW.

See docs/DESIGN_SPEC.md §7.
"""
from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cadet"))
from energy_postmodel import ergun_dp           # noqa: E402

FACTORS = ["T_ads_C", "RH_ads_pct", "T_reg_C", "u_face_m_s", "L_bed_mm", "d_p_mm", "t_half_h"]
# frozen design point for the annual sweep
DESIGN = dict(u_face_m_s=0.3, L_bed_mm=90.0, d_p_mm=2.0, t_half_h=12.0)
EPS, RHO_BULK, DIAM_M = 0.38, 750.0, 0.10


def load_model(name):
    with open(ROOT / "surrogate" / "models" / f"{name}.pkl", "rb") as f:
        d = pickle.load(f)
    return d["model"], d["lo"], d["hi"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites", nargs="+", required=True, help="site:hourlycsv pairs handled upstream")
    ap.add_argument("--cycles-dir", default=str(ROOT / "data" / "climate"))
    ap.add_argument("--gel-m3", type=float, default=1.0, help="total sorbent bed volume [m3]")
    args = ap.parse_args()

    mw_m, lo, hi = load_model("m_w_kg")
    q_m, _, _ = load_model("Q_reg_J")

    area = np.pi * (DIAM_M / 2.0) ** 2
    L = DESIGN["L_bed_mm"] / 1000.0
    dp = DESIGN["d_p_mm"] / 1000.0
    u = DESIGN["u_face_m_s"]
    t_half = DESIGN["t_half_h"] * 3600.0
    dP = ergun_dp(u, L, dp, EPS)
    E_fan_cycle = dP * u * area * t_half                  # J/cycle/module (parasitic)
    V_module = area * L                                   # m3 of bed per module
    n_mod = args.gel_m3 / V_module                        # modules to realise gel-m3
    m_gel = RHO_BULK * args.gel_m3                        # total dry gel mass [kg]

    summ = []
    for site in args.sites:
        cyc = Path(args.cycles_dir) / f"cycles_{site}.csv"
        if not cyc.exists():
            print(f"  [skip] no cycles for {site}"); continue
        rows = list(csv.DictReader(open(cyc)))
        X = np.array([[float(r["T_ads_C"]), float(r["RH_ads_pct"]), float(r["T_reg_C"]),
                       u, DESIGN["L_bed_mm"], DESIGN["d_p_mm"], DESIGN["t_half_h"]] for r in rows])
        Xs = (X - lo) / (hi - lo)
        m_w = np.clip(mw_m.predict_values(Xs).ravel(), 0, None)     # kg/cycle
        Q_reg = np.clip(q_m.predict_values(Xs).ravel(), 0, None)    # J/cycle

        water_kg = float(m_w.sum()) * n_mod
        thermal_kWh = float(Q_reg.sum() / 3.6e6) * n_mod
        fan_kWh = len(rows) * E_fan_cycle / 3.6e6 * n_mod
        sec_elec = fan_kWh / water_kg if water_kg else float("inf")
        sec_tot = (thermal_kWh + fan_kWh) / water_kg if water_kg else float("inf")

        out = ROOT / "results" / f"annual_{site}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doy", "T_ads_C", "RH_ads_pct", "T_reg_C", "m_w_kg", "Q_reg_J"])
            for i, r in enumerate(rows):
                w.writerow([r["doy"], r["T_ads_C"], r["RH_ads_pct"], r["T_reg_C"],
                            f"{m_w[i]:.5f}", f"{Q_reg[i]:.4g}"])
        print(f"[{site}] cycles={len(rows)}  water={water_kg:.2f} kg/yr ({water_kg/m_gel:.1f} L/kg-gel/yr)"
              f"  SEC_elec={sec_elec:.3f} SEC_tot={sec_tot:.2f} kWh/kg")
        summ.append(dict(site=site, cycles=len(rows), water_kg_yr=water_kg, m_gel_kg=m_gel,
                         thermal_kWh_yr=thermal_kWh, fan_kWh_yr=fan_kWh,
                         sec_elec_kWh_kg=sec_elec, sec_tot_kWh_kg=sec_tot,
                         dP_Pa=dP, area_m2=area, L_bed_m=L))

    s_out = ROOT / "results" / "annual_summary.csv"
    if summ:
        with open(s_out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summ[0].keys())); w.writeheader()
            for s in summ:
                w.writerow(s)
        print(f"wrote {s_out}")


if __name__ == "__main__":
    main()
