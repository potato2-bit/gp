#!/usr/bin/env python3
"""Levelised cost of water (LCOW) — Gate G4.

LCOW = (CRF*CAPEX + OPEX_annual) / Water_annual, CRF from i,n in ../project_inputs.yaml.
CAPEX = sorbent + vessel + solar collector + fan + condenser + controls.
OPEX  = fan parasitic electricity (from Ergun dP) + maintenance + periodic sorbent swap.
Reads results/annual_summary.csv (climate/run_annual.py). Compares to anchors:
condensation AWH ~$0.09-0.17/L; reports per-liter LCOW per site.

See docs/DESIGN_SPEC.md §8, Appendix B §7.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# --- cost assumptions (documented; replace with vendor quotes) --------------
C_GEL_USD_KG      = 4.0     # silica gel, bulk
C_COLLECTOR_USD_M2 = 150.0  # flat-plate solar thermal collector
C_VESSEL_USD_KG   = 6.0     # vessel + ducting per kg gel (scales with bed)
C_FIXED_USD       = 250.0   # fan + condenser + controls (per module)
DAILY_SOLAR_J_M2  = 2.16e7  # ~6 kWh/m2/day usable (Egypt clear-sky)
COLL_ETA          = 0.55
MAINT_FRAC        = 0.02    # /yr of CAPEX
GEL_LIFE_YR       = 5       # sorbent replacement interval


def crf(i: float, n: int) -> float:
    """Capital recovery factor."""
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


def lcow_for(s, i, n, elec_usd_kwh, egp):
    water_L = float(s["water_kg_yr"])               # 1 kg water = 1 L
    m_gel = float(s["m_gel_kg"])
    thermal_kWh = float(s["thermal_kWh_yr"])
    fan_kWh = float(s["fan_kWh_yr"])

    # solar collector sized to the peak daily regen heat
    daily_thermal_J = thermal_kWh / float(s["cycles"]) * 3.6e6
    A_coll = daily_thermal_J / (DAILY_SOLAR_J_M2 * COLL_ETA)

    capex = (m_gel * C_GEL_USD_KG + m_gel * C_VESSEL_USD_KG
             + A_coll * C_COLLECTOR_USD_M2 + C_FIXED_USD)
    opex = (fan_kWh * elec_usd_kwh + MAINT_FRAC * capex
            + (m_gel * C_GEL_USD_KG) / GEL_LIFE_YR)
    annualised = crf(i, n) * capex + opex
    lcow = annualised / water_L if water_L > 0 else float("inf")
    return dict(site=s["site"], water_L_yr=water_L, A_coll_m2=A_coll,
                capex_EGP=capex * egp, opex_EGP_yr=opex * egp,
                lcow_EGP_L=lcow * egp, lcow_USD_L=lcow)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", default=str(ROOT / "results" / "annual_summary.csv"))
    ap.add_argument("--inputs", default=str(ROOT.parent / "project_inputs.yaml"))
    ap.add_argument("--label", default="gel")
    ap.add_argument("--egp-rate", type=float, default=49.0, help="EGP per USD")
    args = ap.parse_args()

    econ = yaml.safe_load(open(args.inputs))["economics"]
    i = float(econ["discount_rate_i"]); n = int(econ["project_life_years"])
    elec = float(econ["electricity_USD_per_kWh"])
    egp = args.egp_rate

    rows = list(csv.DictReader(open(args.summary)))
    res = [lcow_for(s, i, n, elec, egp) for s in rows]

    print(f"[{args.label}] CRF(i={i}, n={n}) = {crf(i,n):.5f}   elec = {elec*egp:.2f} EGP/kWh   rate = {egp} EGP/USD")
    print(f"\n{'site':16s} {'water L/yr':>10s} {'CAPEX EGP':>11s} {'OPEX EGP/yr':>11s} {'LCOW EGP/L':>11s} {'(USD/L)':>9s}")
    print("-" * 74)
    for r in res:
        print(f"{r['site']:16s} {r['water_L_yr']:10.0f} {r['capex_EGP']:11.0f} "
              f"{r['opex_EGP_yr']:11.0f} {r['lcow_EGP_L']:11.2f} {r['lcow_USD_L']:9.3f}")
    print(f"\nanchors: condensation AWH ~{0.09*egp:.0f} (on-PV) - {0.17*egp:.0f} (grid) EGP/L")

    out = ROOT / "results" / f"lcow_{args.label}_EGP.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader()
        for r in res:
            w.writerow(r)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
