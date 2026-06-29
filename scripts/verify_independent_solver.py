"""
===================================================================
Script:      verify_independent_solver.py
Author:      Independent verification (Task 9 / #13)
Date:        2026-06-02
Purpose:     STANDALONE re-implementation of the TEC Mode-A/B
             atmospheric-water operating-point solver. Written from
             the governing equations only -- it does NOT import or
             reuse tec_robot_design.py. Its sole job is to confirm,
             via a second independent code path, the headline results:
                 per-tile  ~ 5.35 L/yr
                 mean COP  ~ 1.44
                 mode split ~ 24% A / 36% B / 40% off
Units:       SI; temperatures in deg C at I/O, kelvin internally.
References:  TEC max-parameter model (Luo 2022; Riffat 2003);
             Buck 1981; Magnus/Lawrence 2005; Lewis analogy.
===================================================================
"""
import numpy as np
import pandas as pd
import json, os

# ── Constants (re-entered independently from the datasheet/site) ──────────
ELEV = 180.0
PATM = 101.325 * (1.0 - 2.25577e-5 * ELEV) ** 5.2559     # kPa
RHO, CPA, CPV, KAIR, NU, PR = 1.15, 1006.0, 1860.0, 0.026, 1.6e-5, 0.707
LE = 0.845
MW, RU = 0.018015, 8.314

IMAX, UMAX, DTMAX, THREF = 6.0, 15.4, 66.0, 300.15
ALPHA = UMAX / THREF
RES   = (UMAX / IMAX) * (THREF - DTMAX) / THREF
KTH   = (UMAX * IMAX * (THREF - DTMAX)) / (2.0 * THREF * DTMAX)

ACOLD, VFACE, LCHAR = 0.05, 2.0, 0.05
RTH_HS, DT_MARGIN, TC_FROST = 0.15, 5.0, 1.0
NIGHT_START, NIGHT_END = 18, 6

# ── Independent transport coefficients ────────────────────────────────────
RE   = VFACE * LCHAR / NU
NU_L = 0.664 * RE ** 0.5 * PR ** (1.0 / 3.0)
HCONV = NU_L * KAIR / LCHAR
CPM   = CPA + 0.0 * CPV
HMASS = HCONV / (RHO * CPM * LE ** (2.0 / 3.0))

def psat(T):                     # Buck, kPa
    return 0.61121 * np.exp((18.678 - T / 234.5) * T / (257.14 + T))

def tdew(T, RH):                 # Magnus, deg C
    a, b = 17.625, 243.04
    RH = max(RH, 1e-3)
    g = np.log(RH / 100.0) + a * T / (b + T)
    return b * g / (a - g)

def rho_v(P_kPa, T):             # vapour density, kg/m3
    return P_kPa * 1000.0 * MW / (RU * (T + 273.15))

def hfg(T):                      # J/kg
    return (2500.0 - 2.35 * T) * 1000.0

def loads(Tair, rva, Tc):
    """Latent+sensible cold-side load and condensate rate at plate temp Tc."""
    rvs = rho_v(psat(Tc), Tc)
    md  = HMASS * ACOLD * max(rva - rvs, 0.0)
    Ql  = md * hfg(Tc)
    Qs  = HCONV * ACOLD * max(Tair - Tc, 0.0)
    return md, Qs + Ql

def operating_point(Tair, RH):
    """
    Independent solver. Returns (mode, mdot[kg/s], W[W], COP).
    Mode A : current to HOLD Tc_set is feasible (0<I<=Imax)  -> high COP
    Mode B : capacity-limited; run at Imax, plate floats up   -> low COP
    off    : no net condensation possible
    Different structure from the original: I bracket the hot side by a
    fixed-point sweep and solve Mode-A current from the cold-side balance
    Qc(I)=Qload via the quadratic root; Mode-B plate by 200-step bisection.
    """
    Td = tdew(Tair, RH)
    Tc_set = max(Td - DT_MARGIN, TC_FROST)
    if Tc_set >= Tair - 0.5:
        return 'off', 0.0, 0.0, 0.0
    rva = rho_v((RH / 100.0) * psat(Tair), Tair)
    if rva <= rho_v(psat(Tc_set), Tc_set):
        return 'off', 0.0, 0.0, 0.0

    Th = Tair + 5.0
    mode, I, W, Qc, mdot, Tc = 'A', 0.0, 0.0, 0.0, 0.0, Tc_set
    for _ in range(80):                         # hot-side fixed point
        ThK = Th + 273.15
        md_t, Ql_t = loads(Tair, rva, Tc_set)
        TcK = Tc_set + 273.15
        # Qc(I) = alpha*I*TcK - 0.5 I^2 R - K(ThK-TcK) = Ql_t  -> quadratic in I
        A2 = 0.5 * RES
        B2 = -ALPHA * TcK
        C2 = Ql_t + KTH * (ThK - TcK)
        disc = B2 * B2 - 4 * A2 * C2
        Iset = (-B2 - np.sqrt(disc)) / (2 * A2) if disc >= 0 else None
        if (Iset is not None) and (0.0 < Iset <= IMAX):
            mode, I, Tc, mdot, Qc = 'A', Iset, Tc_set, md_t, Ql_t
        else:
            mode, I = 'B', IMAX
            # solve plate temp where Qc(Imax,Tc) = load(Tc) by bisection
            def resid(Tcx):
                TcxK = Tcx + 273.15
                Qtec = ALPHA * I * TcxK - 0.5 * I * I * RES - KTH * (ThK - TcxK)
                _, Ql = loads(Tair, rva, Tcx)
                return Qtec - Ql
            lo, hi = Tc_set, Tair
            flo, fhi = resid(lo), resid(hi)
            if flo >= 0:
                Tc = Tc_set
            elif fhi <= 0:
                Tc = hi
            else:
                for _b in range(200):
                    mid = 0.5 * (lo + hi)
                    if resid(mid) > 0: hi = mid
                    else: lo = mid
                Tc = 0.5 * (lo + hi)
            mdot, Qc = loads(Tair, rva, Tc)
        dT = (Th + 273.15) - (Tc + 273.15)
        W  = ALPHA * I * dT + I * I * RES
        Th_new = Tair + (Qc + W) * RTH_HS
        if abs(Th_new - Th) < 0.02:
            Th = Th_new; break
        Th = 0.5 * Th + 0.5 * Th_new
    COP = Qc / W if W > 1e-9 else 0.0
    return mode, mdot, W, COP

if __name__ == "__main__":
    base = "/sessions/gallant-laughing-meitner/mnt/GRADUATION PROJECT"
    # local path fallback for portability
    if not os.path.exists(base):
        base = os.path.join(os.path.dirname(__file__), "..")
    df = pd.read_csv(os.path.join(base, "output", "nasa_power_hourly.csv"))
    df["hour"] = (df["datetime"] // 1 % 100).astype(int)   # last 2 digits = hour
    df["hour"] = df["datetime"].astype(str).str[8:10].astype(int)

    print(f"[indep] h_conv={HCONV:.3f}  h_mass={HMASS:.5f}")
    print(f"[indep] alpha={ALPHA:.5f}  R={RES:.4f}  K={KTH:.4f}")

    nA = nB = noff = 0
    water_kg = 0.0; Wh = 0.0; cop_sum = 0.0; cop_n = 0
    for _, r in df.iterrows():
        h = r["hour"]
        if not (h >= NIGHT_START or h < NIGHT_END):
            continue
        mode, md, W, cop = operating_point(r["T2M"], r["RH2M"])
        if mode == 'A':
            nA += 1
            water_kg += md * 3600.0          # smart strategy: harvest Mode A only
            Wh += W
            cop_sum += cop; cop_n += 1
        elif mode == 'B':
            nB += 1
        else:
            noff += 1
    ntot = nA + nB + noff
    water_L = water_kg / 1.0                  # 1 kg ~ 1 L
    mean_cop = cop_sum / cop_n if cop_n else 0.0
    print(f"\n[indep smart] per-tile water = {water_L:.2f} L/yr")
    print(f"[indep smart] energy        = {Wh/1000:.2f} kWh/yr")
    print(f"[indep smart] mean COP (A)   = {mean_cop:.3f}")
    print(f"[indep smart] SEC            = {(Wh/1000)/water_L:.2f} kWh/L")
    print(f"[indep] mode split: A={100*nA/ntot:.1f}%  B={100*nB/ntot:.1f}%  off={100*noff/ntot:.1f}%")

    J = json.load(open(os.path.join(base, "output", "tec_robot_results.json")))
    rep = J["per_tile"]
    print("\n=== COMPARISON vs original engine (JSON) ===")
    def line(name, a, b):
        d = 100*abs(a-b)/abs(b) if b else 0
        print(f"  {name:14s} indep={a:8.3f}  orig={b:8.3f}  diff={d:5.2f}%  {'OK' if d<3 else 'CHECK'}")
    line("water L/yr", water_L, rep["water_Lyr"])
    line("energy kWh/yr", Wh/1000, rep["energy_kWhyr"])
    line("mean COP", mean_cop, rep["mean_COP"])
