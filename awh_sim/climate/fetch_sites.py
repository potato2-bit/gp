#!/usr/bin/env python3
"""Fetch hourly NASA POWER climate for all Egyptian sites (awh_sim_config.yaml).

Pulls T2M, RH2M, ALLSKY_SFC_SW_DWN, WS2M, PRECTOTCORR for one calendar year per site
from the NASA POWER hourly point API and writes data/climate/nasa_power_hourly_<site>.csv.
Reuses the parent fetcher's endpoint/parse structure (stdlib urllib, no extra deps).

See docs/DESIGN_SPEC.md §7, Appendix B §6.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def fetch_site(lat, lon, start, end, community, params):
    q = urlencode(dict(parameters=",".join(params), community=community,
                       longitude=lon, latitude=lat, start=start, end=end, format="JSON"))
    url = f"{ENDPOINT}?{q}"
    with urlopen(url, timeout=120) as r:
        data = json.load(r)
    P = data["properties"]["parameter"]
    times = sorted(P[params[0]].keys())
    rows = []
    for t in times:
        row = {"datetime": t}
        for p in params:
            v = P.get(p, {}).get(t, "")
            row[p] = "" if v in (None, -999, -999.0) else v
        rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "awh_sim_config.yaml"))
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these site names")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    npc = cfg["climate"]["nasa_power"]
    params = npc["parameters"]
    start, end, community = npc["start_date"], npc["end_date"], npc["community"]
    outdir = ROOT / "data" / "climate"
    outdir.mkdir(parents=True, exist_ok=True)

    for s in cfg["climate"]["sites"]:
        if args.only and s["name"] not in args.only:
            continue
        out = outdir / f"nasa_power_hourly_{s['name']}.csv"
        try:
            rows = fetch_site(s["lat"], s["lon"], start, end, community, params)
            with open(out, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["datetime", *params])
                w.writeheader()
                w.writerows(rows)
            print(f"[ok] {s['name']:14s} {len(rows)} hrs -> {out.name}")
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {s['name']}: {type(e).__name__}: {str(e)[:90]}")


if __name__ == "__main__":
    main()
