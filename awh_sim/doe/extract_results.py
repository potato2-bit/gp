#!/usr/bin/env python3
"""Extract high-fi (OpenFOAM) responses → data/openfoam_responses.csv.

Walks cases/run_*/postProcessing/, reads functionObject .dat outputs, computes the
scalar response reductions (m_w, Q_reg, SEC, T_peak, dP, breakthrough scalars) and writes
one row per case keyed by case id (joined to the DoE table by id). Mirrors the CADET
response schema so the two feed the MFK surrogate.

See docs/DESIGN_SPEC.md §5, Appendix B §3.  Status: STUB — implement in Step 4.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cases", default=str(ROOT / "cases"))
    ap.add_argument("--out", default=str(ROOT / "data" / "openfoam_responses.csv"))
    ap.parse_args()
    raise NotImplementedError("Step 4: parse postProcessing → responses CSV.")


if __name__ == "__main__":
    main()
