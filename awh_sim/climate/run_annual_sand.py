#!/usr/bin/env python3
"""Desert-sand baseline — same annual pipeline, near-inert sorbent.

Replaces silica gel with desert (quartz) sand to quantify how much the *sorbent* matters.
Sand has ~3 orders of magnitude less surface area than silica gel (BET ~0.1-1 vs 600-700
m2/g), so its water uptake is tiny. Modelled with a small power-law isotherm
  q_sand*(RH) = A_SAND * RH_frac^N_SAND   [kg/kg]
(A_SAND=0.003, N_SAND=1.5 -> ~0.3% at saturation, ~0.05% at RH 0.3 — an order-of-magnitude
literature value for sand/soil hygroscopic moisture). Regeneration heat is dominated by
sensible heating of the (dense) sand mass, which makes its SEC very poor.

Writes results/annual_summary_sand.csv (same schema as the gel summary) for LCOW.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cadet"))
from energy_postmodel import ergun_dp           # noqa: E402

# --- sand properties (documented order-of-magnitude) ------------------------
SAND_BULK = 1600.0      # kg/m3 dry desert sand bulk density
CP_SAND   = 830.0       # J/kg/K quartz sand
DP_SAND   = 0.3e-3      # m medium sand grain
EPS_SAND  = 0.40
A_SAND    = 0.003       # kg/kg uptake at RH=1
N_SAND    = 1.5
DH_SAND   = 2.4e6       # J/kg (physisorption; swing is tiny so this is minor)

DESIGN = dict(u_face_m_s=0.3, L_bed_mm=90.0, t_half_h=12.0)


def q_sand(rh_frac):
    return A_SAND * max(rh_frac, 0.0) ** N_SAND


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites", nargs="+", required=True)
    ap.add_argument("--cycles-dir", default=str(ROOT / "data" / "climate"))
    ap.add_argument("--gel-m3", type=float, default=1.0, help="bed volume [m3] (same as gel case)")
    args = ap.parse_args()

    L = DESIGN["L_bed_mm"] / 1000.0
    u = DESIGN["u_face_m_s"]
    t_half = DESIGN["t_half_h"] * 3600.0
    A_total = args.gel_m3 / L                    # m2 flow cross-section for the bed volume
    m_sand = SAND_BULK * args.gel_m3
    dP = ergun_dp(u, L, DP_SAND, EPS_SAND)       # fine grains -> high resistance
    E_fan_cycle = dP * u * A_total * t_half       # J/cycle

    summ = []
    for site in args.sites:
        cyc = Path(args.cycles_dir) / f"cycles_{site}.csv"
        if not cyc.exists():
            print(f"  [skip] no cycles for {site}"); continue
        rows = list(csv.DictReader(open(cyc)))
        water = thermal = 0.0
        for r in rows:
            rh = float(r["RH_ads_pct"]) / 100.0
            dq = q_sand(rh)                       # full swing (regenerates to ~0)
            water += dq * m_sand                  # kg/cycle
            dT = float(r["T_reg_C"]) - float(r["T_ads_C"])
            thermal += m_sand * CP_SAND * dT + DH_SAND * dq * m_sand
        water_kg = water
        thermal_kWh = thermal / 3.6e6
        fan_kWh = len(rows) * E_fan_cycle / 3.6e6
        sec_elec = fan_kWh / water_kg if water_kg else float("inf")
        sec_tot = (thermal_kWh + fan_kWh) / water_kg if water_kg else float("inf")
        print(f"[{site}] sand water={water_kg:.1f} kg/yr  SEC_elec={sec_elec:.3f} SEC_tot={sec_tot:.2f} kWh/kg")
        summ.append(dict(site=site, cycles=len(rows), water_kg_yr=water_kg, m_gel_kg=m_sand,
                         thermal_kWh_yr=thermal_kWh, fan_kWh_yr=fan_kWh,
                         sec_elec_kWh_kg=sec_elec, sec_tot_kWh_kg=sec_tot,
                         dP_Pa=dP, area_m2=A_total, L_bed_m=L))

    out = ROOT / "results" / "annual_summary_sand.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0].keys())); w.writeheader()
        for s in summ:
            w.writerow(s)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
