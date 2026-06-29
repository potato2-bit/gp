#!/usr/bin/env python3
"""Passive (fan-off) vs forced-flow penalty — validated with CADET, not assumed.

A passive nested-cube has no fan: air moves by weak natural convection (face velocity
~0.003-0.05 m/s) instead of the forced 0.1-1.0 m/s. Over a ~12 h night the question is
whether that still delivers enough air and lets the bed reach equilibrium loading. We
sweep u at a representative family operating point and report water-per-cycle vs the
forced-flow reference (u = 0.3 m/s). Fan parasitic is zero in the passive case.

Writes data/passive_penalty.csv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cadet"))
import build_column as bc                       # noqa: E402
from energy_postmodel import ergun_dp           # noqa: E402

M_WATER = 0.018015
DIAM = 0.10

# representative family operating point (humid-Delta night, solar regen)
OP = dict(T_C=18.0, RH_in=0.55, T_reg_C=80.0, L_bed_m=0.09, d_p_m=0.002, t_half_h=12.0)
U_LIST = [0.003, 0.005, 0.01, 0.02, 0.05, 0.1, 0.3]
U_REF = 0.3


def water_for(u, params):
    eps = params["bed"]["porosity"]; rho_bulk = params["bed"]["rho_bulk_kg_m3"]
    run = dict(T_C=OP["T_C"], RH_in=OP["RH_in"], L_bed_m=OP["L_bed_m"], diameter_m=DIAM,
               d_p_m=OP["d_p_m"], u_face_m_s=u, t_end_s=OP["t_half_h"] * 3600.0, ncol=60)
    proc, meta = bc.build_column(params, run)
    t, c_out, solid, _ = bc.run_breakthrough(proc, n_time=400)
    q_kgkg = float(np.mean(solid[-1, :, 0])) * M_WATER * (1 - eps) / rho_bulk
    area = np.pi * (DIAM / 2) ** 2
    m_gel = rho_bulk * area * OP["L_bed_m"]
    m_w = q_kgkg * m_gel
    # front traverse fraction over the half-cycle (diagnostic of air-limiting)
    u_front = u * eps * 1.2 * meta["c_in"] * M_WATER / ((1 - eps) * rho_bulk * max(q_kgkg, 1e-9))
    frac = min(1.0, u_front * OP["t_half_h"] * 3600.0 / OP["L_bed_m"])
    dP = ergun_dp(u, OP["L_bed_m"], OP["d_p_m"], eps)
    fan_W = dP * u * area
    return m_w, q_kgkg, frac, fan_W


def main():
    params = bc.load_params(str(ROOT / "awh_sim_config.yaml"))
    rows = []
    ref = None
    for u in U_LIST:
        m_w, q, frac, fan = water_for(u, params)
        if abs(u - U_REF) < 1e-9:
            ref = m_w
        rows.append([u, m_w, q, frac, fan])
    out = ROOT / "data" / "passive_penalty.csv"
    print(f"operating point: T_ads={OP['T_C']} C, RH={OP['RH_in']*100:.0f}%, "
          f"T_reg={OP['T_reg_C']} C, t_half={OP['t_half_h']} h\n")
    print(f"{'u [m/s]':>8} {'water/cyc[kg]':>13} {'q[kg/kg]':>9} {'bed loaded':>11} "
          f"{'fan [W]':>8} {'vs forced':>9}")
    print("-" * 64)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["u_m_s", "water_kg_cycle", "q_kgkg", "bed_loaded_frac", "fan_W", "ratio_vs_forced"])
        for u, m_w, q, frac, fan in rows:
            ratio = m_w / ref if ref else float("nan")
            mode = "(forced ref)" if abs(u - U_REF) < 1e-9 else ("PASSIVE" if u <= 0.05 else "")
            print(f"{u:8.3f} {m_w:13.4f} {q:9.4f} {frac*100:10.0f}% {fan:8.3f} {ratio:8.2f}  {mode}")
            w.writerow([u, m_w, q, frac, fan, ratio])
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
