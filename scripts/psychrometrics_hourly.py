#!/usr/bin/env python3
"""
Optional seasonal analysis: from NASA POWER hourly CSV, compute saturation vapor
pressure (Magnus), humidity ratio omega (kg/kg), and a *theoretical* condensate
ceiling if air were cooled to T_dp (dew point) — illustrative only.

Outputs:
  output/psychrometrics_monthly.csv — monthly mean T, RH, omega

Requires: csv in stdlib only
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "output" / "nasa_power_hourly.csv"
OUT = ROOT / "output" / "psychrometrics_monthly.csv"

# Standard atmosphere pressure for elevation ~180 m (approx 101325 Pa)
P_ATM_PA = 101325.0


def p_ws_pa(T_c: float) -> float:
    """Magnus formula saturation vapor pressure over water (Pa), T in °C."""
    import math

    return 611.2 * math.exp(17.67 * T_c / (T_c + 243.5))


def omega_kg_kg(T_c: float, rh_pct: float) -> float:
    p_w = (rh_pct / 100.0) * p_ws_pa(T_c)
    return 0.621945 * p_w / (P_ATM_PA - p_w)


def main():
    if not INP.exists():
        print("Run scripts/fetch_nasa_power.py first; missing", INP)
        return

    monthly_T: dict[int, list[float]] = defaultdict(list)
    monthly_RH: dict[int, list[float]] = defaultdict(list)
    monthly_om: dict[int, list[float]] = defaultdict(list)

    with open(INP, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                dt = datetime.strptime(row["datetime"], "%Y%m%d%H")
            except (KeyError, ValueError):
                continue
            try:
                t2m = float(row.get("T2M", "") or "")
                rh = float(row.get("RH2M", "") or "")
            except ValueError:
                continue
            m = dt.month
            monthly_T[m].append(t2m)
            monthly_RH[m].append(rh)
            monthly_om[m].append(omega_kg_kg(t2m, rh))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "month",
                "T2M_mean_C",
                "RH2M_mean_pct",
                "omega_mean_kg_kg",
            ]
        )
        for m in range(1, 13):
            if not monthly_T[m]:
                continue
            Tbar = sum(monthly_T[m]) / len(monthly_T[m])
            RHbar = sum(monthly_RH[m]) / len(monthly_RH[m])
            ombar = sum(monthly_om[m]) / len(monthly_om[m])
            w.writerow([m, f"{Tbar:.3f}", f"{RHbar:.3f}", f"{ombar:.6f}"])

    print("Wrote:", OUT)


if __name__ == "__main__":
    main()
