#!/usr/bin/env python3
"""Render OpenFOAM cases from the high-fi DoE rows (Jinja2 templating).

For each high-fi row of data/doe_design.csv, render cases/template/ (blockMeshDict,
bed/transport properties, 0/ fields, controlDict) into cases/run_XXXX/ with the row's
factor values substituted. Bed length/diameter drive blockMeshDict geometry; particle
diameter/porosity drive the Ergun d,f and LDF coefficients.

See docs/DESIGN_SPEC.md §9 and Appendix B §4.  Status: STUB — implement in Step 4.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--design", default=str(ROOT / "data" / "doe_design.csv"))
    ap.add_argument("--template", default=str(ROOT / "cases" / "template"))
    ap.parse_args()
    raise NotImplementedError("Step 4: Jinja2 render high-fi rows → cases/run_XXXX/.")


if __name__ == "__main__":
    main()
