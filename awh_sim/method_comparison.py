#!/usr/bin/env python3
"""Head-to-head AWH method comparison over the 6 Egyptian sites.

Three methods on the SAME aggregated climate cycles (data/climate/cycles_<site>.csv):
  A. Silica gel           — Tier-0 Sips isotherm (this project's validated material)
  B. Silica-gel/CaCl2     — composite "selective water sorbent" (SWS-1L-type), stronger
                            low-RH uptake (literature-form isotherm w = a*RH^n)
  C. PV vapour-compression condensation — psychrometric model; only works above ~30-35% RH

Reports per site per method: works?, annual water (per defined unit), SEC, LCOW (EGP/L).
Intensive metrics (SEC, LCOW) are the fair comparators; annual water uses a stated unit.
Writes results/method_comparison.csv and results/method_comparison.png.

Caveats: composite isotherm + costs are order-of-magnitude literature estimates (Aristov
SWS); condensation COP/coil fixed. Relative pattern is robust; absolute numbers indicative.
"""
from __future__ import annotations
import csv, math
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
SITES = ["aswan_benban", "mansoura", "new_alamein", "hurghada", "siwa", "nac"]

# --- constants ---
RHO_SORB = 750.0      # kg/m3 packed sorbent (both gel and composite, ~similar)
M_W = 0.018015; R = 8.314462618; T0 = 273.15; PTOT = 101325.0
CP_AIR = 1020.0; H_FG = 2.45e6; RHO_AIR = 1.2
COP = 3.0; T_COIL = 7.0                     # condensation refrigeration
EGP = 49.0; ELEC = 0.98                     # EGP/kWh (grid)
CRF = 0.11683                               # i=0.08, n=15

# Tier-0 Sips (silica gel) from data/isotherm/params.yaml
QM, KREF, DHK, N0, N1, TREFC = 0.39079712878744455, 3.707238835550887e-05, -99414.09542067378, \
    0.6819637278159347, -0.017811620676531893, 30.0
# composite SWS-1L-type working isotherm  w = a*RH^n  (kg/kg), conservative literature form
A_CMP, N_CMP = 0.40, 0.75


def psat(T_C):
    return 611.21 * math.exp((18.678 - T_C / 234.5) * (T_C / (257.14 + T_C)))


def q_sips(T_C, Pv):
    inv = 1.0 / (T_C + T0) - 1.0 / (TREFC + T0)
    K = KREF * math.exp(-DHK / R * inv)
    n = min(1.0, max(0.1, N0 + N1 * (T_C - 25.0)))
    KP = max(K * Pv, 0.0) ** n
    return QM * KP / (1.0 + KP)


def w_comp(RH):
    return A_CMP * max(RH, 0.0) ** N_CMP


def omega(T_C, RH):
    Pv = RH * psat(T_C)
    return 0.622 * Pv / (PTOT - Pv)


def cycles(site):
    f = ROOT / "data" / "climate" / f"cycles_{site}.csv"
    return list(csv.DictReader(open(f)))


def sorption_site(site, kind):
    """kind: 'silica' or 'composite'. 1 m3 sorbent. Returns dict of metrics."""
    m = RHO_SORB * 1.0
    cp = 921.0 if kind == "silica" else 1000.0
    dH = 2.4e6 if kind == "silica" else 2.8e6
    c_sorb = 80.0 if kind == "silica" else 150.0      # EGP/kg
    water = 0.0; therm = 0.0
    for r in cycles(site):
        Ta = float(r["T_ads_C"]); RH = float(r["RH_ads_pct"]) / 100.0; Tr = float(r["T_reg_C"])
        Pv = RH * psat(Ta)
        # near-complete solar regeneration at T_reg (residual ~0), as the validated
        # surrogate assumed; working swing = adsorption-end equilibrium loading
        if kind == "silica":
            dq = q_sips(Ta, Pv)
        else:
            dq = w_comp(RH)
        water += dq * m
        therm += m * cp * (Tr - Ta) + dH * dq * m
    n = len(cycles(site))
    fan_kWh = n * 0.001 * 1.0 / 3.6e6 * 0  # negligible passive fan
    sec_th = therm / 3.6e6 / water if water else float("inf")
    capex = m * c_sorb * 1.5 + 5000.0                  # EGP: sorbent+vessel+collector+frame
    opex = 0.02 * capex + (m * c_sorb) / 8.0           # EGP/yr: maint + sorbent swap (8 yr)
    lcow = (CRF * capex + opex) / water if water else float("inf")   # EGP/L
    return dict(water_L_yr=water, sec_th_kWh_kg=sec_th, sec_el_kWh_kg=0.12,
                lcow_EGP_L=lcow, capex_EGP=capex, works="yes")


def condensation_site(site, airflow_m3h=1000.0, hours=12.0):
    """PV vapour-compression. airflow unit; runs the humid night window."""
    w_coil = omega(T_COIL, 1.0)
    water = 0.0; elec = 0.0; feas_cycles = 0
    mdot = airflow_m3h * RHO_AIR / 3600.0              # kg dry air /s (approx)
    for r in cycles(site):
        Ta = float(r["T_ads_C"]); RH = float(r["RH_ads_pct"]) / 100.0
        dw = omega(Ta, RH) - w_coil
        if dw <= 5e-4:                                  # too dry to condense usefully
            continue
        feas_cycles += 1
        air_kg = mdot * hours * 3600.0
        w_cyc = air_kg * dw                             # kg water this cycle
        q_cool = air_kg * (CP_AIR * (Ta - T_COIL) + dw * H_FG)   # J
        water += w_cyc
        elec += q_cool / COP                            # J electrical
    n = len(cycles(site))
    sec_el = (elec / 3.6e6) / water if water else float("inf")
    daily = water / 365.0
    capex = daily * 150.0                               # ~EGP/(L/day) incl PV (≈$3/L-day)
    opex = sec_el * water * ELEC + 0.03 * capex         # grid elec + maint
    lcow = (CRF * capex + opex) / water if water else float("inf")
    works = "yes" if feas_cycles > n * 0.5 else ("marginal" if feas_cycles > n * 0.15 else "NO")
    return dict(water_L_yr=water, sec_el_kWh_kg=sec_el, lcow_EGP_L=lcow,
                capex_EGP=capex, works=works, feas_frac=feas_cycles / n)


def main():
    rows = []
    print(f"{'site':14} {'method':12} {'works':9} {'water L/yr':>11} {'SEC kWh/L':>10} {'LCOW EGP/L':>11}")
    print("-" * 72)
    for s in SITES:
        a = sorption_site(s, "silica"); b = sorption_site(s, "composite"); c = condensation_site(s)
        for name, d, sec in (("silica_gel", a, a["sec_el_kWh_kg"] + a["sec_th_kWh_kg"]),
                             ("composite", b, b["sec_el_kWh_kg"] + b["sec_th_kWh_kg"]),
                             ("condensation", c, c["sec_el_kWh_kg"])):
            print(f"{s:14} {name:12} {d['works']:9} {d['water_L_yr']:11.0f} {sec:10.2f} {d['lcow_EGP_L']:11.2f}")
            rows.append(dict(site=s, method=name, works=d["works"],
                             water_L_yr=round(d["water_L_yr"]), SEC_kWh_L=round(sec, 2),
                             LCOW_EGP_L=round(d["lcow_EGP_L"], 2)))
        print()
    out = ROOT / "results" / "method_comparison.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"wrote {out}")

    # figure
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import numpy as np
    meth = ["silica_gel", "composite", "condensation"]; col = ["tab:blue", "tab:green", "tab:orange"]
    x = np.arange(len(SITES)); wbar = 0.26
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
    for i, mth in enumerate(meth):
        wv = [next(r["water_L_yr"] for r in rows if r["site"] == s and r["method"] == mth) for s in SITES]
        lv = [next(r["LCOW_EGP_L"] for r in rows if r["site"] == s and r["method"] == mth) for s in SITES]
        ax[0].bar(x + (i - 1) * wbar, wv, wbar, label=mth, color=col[i])
        ax[1].bar(x + (i - 1) * wbar, lv, wbar, label=mth, color=col[i])
    lbl = [s.replace("aswan_", "").replace("new_", "N.") for s in SITES]
    ax[0].set_yscale("log"); ax[0].set_ylabel("annual water [L/yr]"); ax[0].set_title("Water yield (1 m3 sorbent / 1000 m3/h AWG)")
    ax[1].set_ylabel("LCOW [EGP/L]"); ax[1].set_title("Levelised cost (EGP/L)")
    ax[1].axhspan(4, 8, color="gray", alpha=0.12)
    for a_ in ax:
        a_.set_xticks(x); a_.set_xticklabels(lbl, rotation=30, ha="right", fontsize=8); a_.legend(fontsize=8); a_.grid(alpha=0.3, axis="y")
    fig.suptitle("AWH methods across 6 Egyptian sites — silica gel vs CaCl2 composite vs PV condensation", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(ROOT / "results" / "method_comparison.png", dpi=140)
    print("wrote results/method_comparison.png")


if __name__ == "__main__":
    main()
