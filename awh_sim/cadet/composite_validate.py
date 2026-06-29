#!/usr/bin/env python3
"""Simulation-backed check of the CaCl2/silica composite advantage, in CADET (G1 engine).

Replaces the analytic power-law with a literature SWS-1L composite isotherm and runs the
SAME validated CADET breakthrough as the silica-gel case, at a representative passive
family operating point. Reports the composite/silica uptake ratio.

SWS-1L (CaCl2-in-mesoporous-silica, Aristov/Gordeeva): deliquescence-dominated, near-linear
in RH over the working range. We use w*(phi) ~ a*phi (kg/kg), a~0.7 — markedly higher than
silica gel's ~0.1*phi^0.54 at the same RH, especially at low RH.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cadet"))
import build_column as bc                       # noqa: E402

M_WATER = 0.018015

# representative passive family night
RUN = dict(T_C=18.0, RH_in=0.55, L_bed_m=0.09, diameter_m=0.10, d_p_m=0.002,
           u_face_m_s=0.05, t_end_s=12 * 3600.0, ncol=60)

# SWS-1L composite equilibrium isotherm (kg/kg), T in degC, phi=RH fraction
def composite_w(T_C, phi, branch="adsorption"):
    phi = np.asarray(phi, dtype=float)
    return 0.70 * np.clip(phi, 0.0, 1.0)        # deliquescence-dominated, ~linear in RH


def uptake(params):
    proc, meta = bc.build_column(params, RUN)
    t, c_out, solid, _ = bc.run_breakthrough(proc, n_time=400)
    eps = params["bed"]["porosity"]; rho_bulk = params["bed"]["rho_bulk_kg_m3"]
    q_kgkg = float(np.mean(solid[-1, :, 0])) * M_WATER * (1 - eps) / rho_bulk
    return q_kgkg, meta


def main():
    params = bc.load_params(str(ROOT / "awh_sim_config.yaml"))
    print(f"operating point: T={RUN['T_C']} C, RH={RUN['RH_in']*100:.0f}%, "
          f"u={RUN['u_face_m_s']} m/s, t_half={RUN['t_end_s']/3600:.0f} h\n")

    q_si, m_si = uptake(params)
    print(f"  silica gel : FreundlichLDF kf={m_si['kf']:.4g} n={m_si['n']:.3f}  "
          f"uptake q = {q_si:.4f} kg/kg")

    orig = bc.q_star_hraiech
    bc.q_star_hraiech = composite_w          # feed the composite isotherm into the CADET fit
    try:
        q_co, m_co = uptake(params)
    finally:
        bc.q_star_hraiech = orig
    print(f"  composite  : FreundlichLDF kf={m_co['kf']:.4g} n={m_co['n']:.3f}  "
          f"uptake q = {q_co:.4f} kg/kg")

    ratio = q_co / q_si if q_si else float("inf")
    m = 750.0  # 1 m3
    print(f"\n  composite / silica uptake ratio = {ratio:.2f}x  (CADET breakthrough)")
    print(f"  water per cycle, 1 m3 bed:  silica {q_si*m:.0f} kg   composite {q_co*m:.0f} kg")
    print(f"\n  => the ~3x composite advantage is {'CONFIRMED' if ratio >= 2.5 else 'NOT confirmed'} "
          f"in the G1-validated CADET engine.")


if __name__ == "__main__":
    main()
