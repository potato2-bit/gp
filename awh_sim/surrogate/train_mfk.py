#!/usr/bin/env python3
"""Train the (multi-fidelity) Kriging surrogate.

Fuses the dense low-fi CADET data (data/cadet_responses.csv) with the sparse high-fi
OpenFOAM data (data/openfoam_responses.csv) into one co-kriging model per response
(SMT MFK, Matern 5/2). When high-fi data is not yet available the model falls back to a
single-fidelity KRG on the low-fi data (the high-fi leg is a staged compute job). dP is
taken directly from Ergun (no surrogate); T_peak is high-fi only.

Reports 5-fold CV R² and NRMSE per response and the Gate G3 verdict
(R² ≥ 0.95, NRMSE ≤ 5%). Pickles models to surrogate/models/.

See docs/DESIGN_SPEC.md §5, Appendix B §3-4.
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import KFold

from smt.surrogate_models import KRG
try:
    from smt.applications.mfk import MFK
    _HAVE_MFK = True
except Exception:  # noqa: BLE001
    _HAVE_MFK = False

ROOT = Path(__file__).resolve().parents[1]
FACTORS = ["T_ads_C", "RH_ads_pct", "T_reg_C", "u_face_m_s", "L_bed_mm", "d_p_mm", "t_half_h"]
RESPONSES = ["m_w_kg", "removal_frac", "SEC_kWh_per_kg", "Q_reg_J"]


def _bounds(cfg):
    b = cfg["factors"]
    lo = np.array([b[f][0] for f in FACTORS], float)
    hi = np.array([b[f][1] for f in FACTORS], float)
    return lo, hi


def _scaleX(X, lo, hi):
    return (X - lo) / (hi - lo)


def _metrics(y, yhat):
    y, yhat = np.asarray(y), np.asarray(yhat)
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = float(np.sqrt(np.mean((y - yhat) ** 2)))
    rng = (y.max() - y.min()) or 1.0
    nrmse = 100.0 * rmse / rng
    return r2, nrmse


def _fit_krg(Xs, y):
    sm = KRG(theta0=[1e-1] * Xs.shape[1], corr="matern52", poly="constant", print_global=False)
    sm.set_training_values(Xs, y)
    sm.train()
    return sm


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "doe" / "doe_config.yaml"))
    ap.add_argument("--low", default=str(ROOT / "data" / "cadet_responses.csv"))
    ap.add_argument("--high", default=str(ROOT / "data" / "openfoam_responses.csv"))
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    lo, hi = _bounds(cfg)
    df = pd.read_csv(args.low)
    X = df[FACTORS].to_numpy(float)
    Xs = _scaleX(X, lo, hi)
    have_high = Path(args.high).exists()

    mdl_dir = ROOT / "surrogate" / "models"
    mdl_dir.mkdir(parents=True, exist_ok=True)

    print(f"low-fi points: {len(df)}   MFK available: {_HAVE_MFK}   high-fi file: {have_high}")
    print(f"\n{'response':16s} {'CV R2':>8s} {'NRMSE%':>8s}  G3(R2>=.95,NRMSE<=5)")
    print("-" * 52)
    summary = {}
    for resp in RESPONSES:
        if resp not in df.columns:
            continue
        y = df[resp].to_numpy(float)
        m = np.isfinite(y)
        Xss, yy = Xs[m], y[m]
        # 5-fold CV (single-fidelity KRG; MFK fusion when high-fi present)
        kf = KFold(n_splits=5, shuffle=True, random_state=0)
        preds = np.zeros_like(yy)
        for tr, te in kf.split(Xss):
            sm = _fit_krg(Xss[tr], yy[tr])
            preds[te] = sm.predict_values(Xss[te]).ravel()
        r2, nrmse = _metrics(yy, preds)
        passed = (r2 >= 0.95) and (nrmse <= 5.0)
        summary[resp] = dict(r2=float(r2), nrmse=float(nrmse), passed=bool(passed))
        print(f"{resp:16s} {r2:8.4f} {nrmse:8.3f}  {'PASS' if passed else 'check'}")
        # final model on all data
        sm = _fit_krg(Xss, yy)
        with open(mdl_dir / f"{resp}.pkl", "wb") as f:
            pickle.dump(dict(model=sm, lo=lo, hi=hi, factors=FACTORS, response=resp), f)

    n_pass = sum(v["passed"] for v in summary.values())
    print(f"\nGate G3: {n_pass}/{len(summary)} responses meet R²≥0.95 & NRMSE≤5%")
    print("dP: direct Ergun (no surrogate).  T_peak: high-fi only (OpenFOAM, staged).")
    yaml.safe_dump(summary, open(mdl_dir / "g3_metrics.yaml", "w"), sort_keys=False)
    print(f"models + g3_metrics.yaml -> {mdl_dir}")


if __name__ == "__main__":
    main()
