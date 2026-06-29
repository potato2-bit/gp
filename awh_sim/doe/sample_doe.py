#!/usr/bin/env python3
"""Nested multi-fidelity DoE sampler (Sobol').

Generates a Sobol' space-filling design over the 7 factors and tags each row with a
'fidelity' column:
  - 'highfi' : nested subset run in BOTH CADET (low-fi) and OpenFOAM (high-fi)
  - 'lowfi'  : remaining low-fi points (CADET only)
  - 'test'   : independent high-fi test set (Gate G3), OpenFOAM only

Nesting (high-fi ⊂ low-fi) is enforced by taking the first n_highfi points of the same
Sobol' sequence as the high-fi subset, so the co-kriging pairs are exact. Regenerable
bit-for-bit from doe/doe_config.yaml + seed. Writes data/doe_design.csv.

See docs/DESIGN_SPEC.md §6, Appendix B §1.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parents[1]

# canonical factor order (columns)
FACTORS = ["T_ads_C", "RH_ads_pct", "T_reg_C", "u_face_m_s", "L_bed_mm", "d_p_mm", "t_half_h"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(Path(__file__).resolve().parent / "doe_config.yaml"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    seed = int(cfg["seed"])
    n_low = int(cfg["n_lowfi"])
    n_high = int(cfg["n_highfi"])
    n_test = int(cfg["n_test_highfi"])
    bounds = cfg["factors"]
    lo = np.array([bounds[f][0] for f in FACTORS], dtype=float)
    hi = np.array([bounds[f][1] for f in FACTORS], dtype=float)

    # main Sobol' sequence -> low-fi design; nested high-fi = first n_high points
    sob = qmc.Sobol(d=len(FACTORS), scramble=True, seed=seed)
    u_low = sob.random(n_low)
    X_low = qmc.scale(u_low, lo, hi)

    # independent test set (separate stream)
    sob_t = qmc.Sobol(d=len(FACTORS), scramble=True, seed=seed + 777)
    X_test = qmc.scale(sob_t.random(n_test), lo, hi)

    out = Path(args.out) if args.out else ROOT / "data" / "doe_design.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", *FACTORS, "fidelity"])
        for i in range(n_low):
            fid = "highfi" if i < n_high else "lowfi"   # nested high-fi ⊂ low-fi
            w.writerow([f"run_{i:04d}", *[f"{v:.6g}" for v in X_low[i]], fid])
        for j in range(n_test):
            w.writerow([f"test_{j:04d}", *[f"{v:.6g}" for v in X_test[j]], "test"])

    n_rows = n_low + n_test
    print(f"wrote {out}")
    print(f"  low-fi (CADET): {n_low}  (of which nested high-fi: {n_high})")
    print(f"  high-fi test set (OpenFOAM, G3): {n_test}")
    print(f"  total rows: {n_rows}   factors: {FACTORS}")


if __name__ == "__main__":
    main()
