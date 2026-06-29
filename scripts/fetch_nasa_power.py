#!/usr/bin/env python3
"""
Download hourly NASA POWER parameters for Benban coordinates (from project_inputs.yaml).
Saves CSV to output/nasa_power_hourly.csv for psychrometrics script.

Requires: pip install pyyaml requests
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def main():
    try:
        import yaml  # type: ignore
    except ImportError:
        print("pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    with open(ROOT / "project_inputs.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    site = cfg["site"]
    np_cfg = cfg.get("nasa_power", {})
    lat = site["latitude_deg"]
    lon = site["longitude_deg"]
    start = np_cfg.get("start_date", "20200101")
    end = np_cfg.get("end_date", "20201231")
    community = np_cfg.get("community", "RE")
    params = np_cfg.get("parameters", ["T2M", "RH2M", "PRECTOTCORR"])
    param_str = ",".join(params)

    base = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    q = {
        "parameters": param_str,
        "community": community,
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
    }
    url = f"{base}?{urlencode(q)}"
    print("GET", url[:120], "...")

    with urlopen(url, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if data.get("messages"):
        print("API messages:", data["messages"])

    props = data.get("properties", {})
    par = props.get("parameter", {})
    # NASA returns per-parameter time series; align by datetime from first series
    keys = list(par.keys())
    if not keys:
        print("No parameter data in response", file=sys.stderr)
        sys.exit(2)

    # Use first parameter's datetime list
    first = par[keys[0]]
    if isinstance(first, dict):
        times = list(first.keys())
    else:
        print("Unexpected structure", file=sys.stderr)
        sys.exit(2)

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "nasa_power_hourly.csv"
    fieldnames = ["datetime"] + keys
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for t in sorted(times):
            row = {"datetime": t}
            for k in keys:
                series = par[k]
                row[k] = series.get(t) if isinstance(series, dict) else ""
            w.writerow(row)

    print("Wrote:", out_path, "rows:", len(times))


if __name__ == "__main__":
    main()
