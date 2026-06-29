#!/usr/bin/env python3
"""Aggregate hourly climate into per-cycle (daily) surrogate operating inputs.

One adsorb(night)/regen(day) cycle per calendar day:
  - night hours (20:00-06:00): adsorption point T_ads = mean T2M, RH_ads = mean RH2M
  - day hours (09:00-15:00):    T_reg = T_day + collector boost from clear-sky irradiance,
    boost = eta0 * G_clear / a1  (flat-plate relation, awh_sim_config collector block);
    G_clear from a latitude/day-of-year clear-sky peak (cache has no measured irradiance).
Operating inputs are clamped to the surrogate's trained box; clamped cycles are counted.

See docs/DESIGN_SPEC.md §7, Appendix B §6.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "scripts"))

# surrogate trained box (operating factors)
BOX = {"T_ads_C": (5, 30), "RH_ads_pct": (15, 90), "T_reg_C": (60, 120)}


def clear_sky_peak(lat_deg, doy):
    """Crude clear-sky solar-noon GHI [W/m2] from latitude and day-of-year."""
    decl = 23.45 * math.sin(math.radians(360.0 * (284 + doy) / 365.0))
    alt = 90.0 - abs(lat_deg - decl)            # solar-noon altitude
    return max(0.0, 1000.0 * math.sin(math.radians(alt)) * 0.78)  # 0.78 atmospheric


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--site", required=True)
    ap.add_argument("--hourly", required=True)
    ap.add_argument("--config", default=str(ROOT / "awh_sim_config.yaml"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    coll = cfg["collector"]
    eta0, a1 = float(coll["eta0"]), float(coll["a1_W_m2K"])
    sites = {s["name"]: s for s in cfg["climate"]["sites"]}
    lat = float(sites.get(args.site, {}).get("lat", 30.0))

    night = defaultdict(lambda: {"T": [], "RH": []})
    day = defaultdict(lambda: {"T": [], "G": []})
    for row in csv.DictReader(open(args.hourly, encoding="utf-8")):
        try:
            dt = datetime.strptime(row["datetime"], "%Y%m%d%H")
            T = float(row["T2M"]); RH = float(row["RH2M"])
        except (KeyError, ValueError):
            continue
        key = dt.timetuple().tm_yday
        h = dt.hour
        if h >= 20 or h <= 6:
            night[key]["T"].append(T); night[key]["RH"].append(RH)
        if 9 <= h <= 15:
            day[key]["T"].append(T)
            try:
                g = float(row.get("ALLSKY_SFC_SW_DWN", ""))
                if g >= 0:
                    day[key]["G"].append(g)
            except (ValueError, TypeError):
                pass

    out = Path(args.out) if args.out else ROOT / "data" / "climate" / f"cycles_{args.site}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    n_clamp = 0
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["doy", "T_ads_C", "RH_ads_pct", "T_reg_C", "clamped"])
        for doy in sorted(night):
            if not night[doy]["T"] or doy not in day or not day[doy]["T"]:
                continue
            T_ads = sum(night[doy]["T"]) / len(night[doy]["T"])
            RH_ads = sum(night[doy]["RH"]) / len(night[doy]["RH"])
            T_day = sum(day[doy]["T"]) / len(day[doy]["T"])
            # measured daytime irradiance if available, else clear-sky fallback
            Glist = day[doy]["G"]
            G = (sum(Glist) / len(Glist)) if Glist else clear_sky_peak(lat, doy)
            T_reg = T_day + eta0 * G / a1
            cl = 0
            for name, val in (("T_ads_C", T_ads), ("RH_ads_pct", RH_ads), ("T_reg_C", T_reg)):
                loa, hia = BOX[name]
                if val < loa or val > hia:
                    cl = 1
            n_clamp += cl
            T_ads = min(max(T_ads, BOX["T_ads_C"][0]), BOX["T_ads_C"][1])
            RH_ads = min(max(RH_ads, BOX["RH_ads_pct"][0]), BOX["RH_ads_pct"][1])
            T_reg = min(max(T_reg, BOX["T_reg_C"][0]), BOX["T_reg_C"][1])
            w.writerow([doy, f"{T_ads:.3f}", f"{RH_ads:.3f}", f"{T_reg:.3f}", cl])
    print(f"wrote {out}  ({n_clamp} cycles had a clamped operating input)")


if __name__ == "__main__":
    main()
