#!/usr/bin/env python3
"""Validate the surrogate (Gate G3).

k-fold CV + held-out high-fi test set per response. Acceptance: R^2 >= 0.95,
nRMSE <= 5% of range; T_peak also max-abs-err <= 5 degC. Confirms MFK beats a
high-fi-only GP (else falls back per response). Writes parity plots to results/parity/.

See docs/DESIGN_SPEC.md §5, §10.  Status: STUB — implement in Step 4.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "awh_sim_config.yaml"))
    ap.parse_args()
    raise NotImplementedError("Step 4: CV + gates + parity plots (Gate G3).")


if __name__ == "__main__":
    main()
