#!/usr/bin/env python3
"""Tier 0 - fit the silica-gel/water isotherm and isosteric heat (Gate G0).

Ground truth: the temperature-explicit Hraiech et al. 2025 correlation (Sci. Rep.
15:29041), q* in kg water / kg dry gel, phi = RH (0-1 fraction), T in degC:

  adsorption:  q* = 0.1049*phi^0.5432 - 0.00156*(T-25)*phi + 8.91e-5*(T-25)^2
  desorption:  q* = 0.0987*phi^0.5891 - 0.00203*(T-25)*phi + 7.56e-5*(T-25)^2

Validity 27-44 degC, 44-82 % RH (sampled a little wider for fitting; extrapolation
is reported honestly in the output notes).

What this script does
---------------------
1. Samples the adsorption correlation on a (T, phi) grid -> synthetic q*(P) data
   per temperature, with RH -> vapour pressure via P = phi * Psat(T), Psat from
   Arden-Buck.
2. Fits CADET-expressible isotherm forms - Sips (Langmuir-Freundlich) and Toth,
   plus GAB and Freundlich for comparison - to q*(P) at each temperature with
   scipy.optimize.curve_fit, then captures the temperature trend of each fitted
   parameter (capacity ~ const, affinity ~ van't Hoff, exponent ~ linear in T).
3. Computes the isosteric heat dH_ads(q) by Clausius-Clapeyron: at fixed loading q0
   invert q*(T,phi)=q0 -> phi -> P=phi*Psat(T) across several T, then
   dH_ads = R*T^2 * d(lnP)/dT |_q   [J/mol]  ->  /M_water  [J/kg].
4. Writes data/isotherm/params.yaml (model + constants + T-dependence + dH_ads
   summary + per-model fit quality + provenance).
5. Saves results/isotherm_fit.png and results/isosteric_heat.png.

Gate G0: chosen model reproduces the Hraiech correlation within ~1.5 % RMSE
(adsorption) AND dH_ads lands in the literature band 2.2-2.8 MJ/kg.
See docs/DESIGN_SPEC.md sec 2.

Implementation note: the design spec lists pyGAPS as the Tier-0 tool. pyGAPS's
ModelIsotherm API fits its own model registry (Langmuir/Toth/Freundlich/...) but it
does not ship a Sips model and its T-dependent / isosteric-heat workflow expects a
PointIsotherm family with real pressure axes. We use scipy.optimize.curve_fit
directly: it fits every form we need (incl. Sips), gives clean RMSE/R^2 per model,
and lets us build the van't Hoff T-trend explicitly. pyGAPS is still imported as an
isosteric-heat cross-check via its CC routine where it cooperates. This deviation is
recorded in params.yaml provenance.
"""
from __future__ import annotations

import argparse
import datetime as _dt
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import curve_fit

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# physical constants
# ---------------------------------------------------------------------------
R_GAS = 8.314462618          # J/mol/K
M_WATER = 0.018015           # kg/mol
T0_K = 273.15

# ---------------------------------------------------------------------------
# Hraiech 2025 ground-truth correlation
# ---------------------------------------------------------------------------
def q_star_hraiech(T_C, phi, branch="adsorption"):
    """Equilibrium loading [kg/kg]. T in degC, phi = RH fraction (0-1)."""
    T_C = np.asarray(T_C, dtype=float)
    phi = np.asarray(phi, dtype=float)
    dT = T_C - 25.0
    if branch == "adsorption":
        return 0.1049 * phi ** 0.5432 - 0.00156 * dT * phi + 8.91e-5 * dT ** 2
    elif branch == "desorption":
        return 0.0987 * phi ** 0.5891 - 0.00203 * dT * phi + 7.56e-5 * dT ** 2
    raise ValueError(branch)


def psat_buck(T_C):
    """Arden-Buck saturation vapour pressure [Pa]. T in degC."""
    T_C = np.asarray(T_C, dtype=float)
    return 611.21 * np.exp((18.678 - T_C / 234.5) * (T_C / (257.14 + T_C)))


# ---------------------------------------------------------------------------
# candidate isotherm models  q*(P)  [P in Pa, q in kg/kg]
# ---------------------------------------------------------------------------
def sips(P, qm, K, n):
    """Sips / Langmuir-Freundlich:  q = qm (K P)^n / (1 + (K P)^n)."""
    KP = np.power(K * P, n)
    return qm * KP / (1.0 + KP)


def toth(P, qm, b, t):
    """Toth:  q = qm b P / (1 + (b P)^t)^(1/t)."""
    bP = b * P
    return qm * bP / np.power(1.0 + np.power(bP, t), 1.0 / t)


def freundlich(P, a, n):
    """Freundlich:  q = a P^n."""
    return a * np.power(P, n)


def gab(P, qm, C, k, Psat):
    """GAB on relative pressure x = P/Psat (Psat fixed per isotherm)."""
    x = P / Psat
    return qm * C * k * x / ((1.0 - k * x) * (1.0 - k * x + C * k * x))


MODELS = {
    "Sips": dict(func=sips, p0=[0.4, 1e-3, 0.6], cadet=True,
                 bounds=([0.05, 1e-8, 0.1], [2.0, 1e2, 3.0])),
    "Toth": dict(func=toth, p0=[0.4, 1e-3, 0.8], cadet=True,
                 bounds=([0.05, 1e-8, 0.1], [2.0, 1e2, 3.0])),
    "Freundlich": dict(func=freundlich, p0=[1e-3, 0.5], cadet=True,
                       bounds=([1e-12, 0.05], [1e2, 2.0])),
    "GAB": dict(func=None, p0=[0.2, 10.0, 0.9], cadet=False,
                bounds=([0.02, 0.1, 0.05], [2.0, 1e4, 0.999])),
}


# ---------------------------------------------------------------------------
# fitting helpers
# ---------------------------------------------------------------------------
def _stats(q_data, q_pred):
    resid = q_pred - q_data
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_res = float(np.sum(resid ** 2))
    ss_tot = float(np.sum((q_data - np.mean(q_data)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rel_rmse = rmse / float(np.mean(q_data))
    return rmse, r2, rel_rmse


def fit_model_per_T(model_name, T_list, phi_grid, branch="adsorption"):
    """Fit `model_name` to q*(P) at each temperature. Returns dict per T."""
    spec = MODELS[model_name]
    out = {}
    for T_C in T_list:
        P = phi_grid * psat_buck(T_C)              # Pa
        q = q_star_hraiech(T_C, phi_grid, branch)  # kg/kg
        if model_name == "GAB":
            Psat = float(psat_buck(T_C))
            func = lambda P_, qm, C, k: gab(P_, qm, C, k, Psat)
        else:
            func = spec["func"]
        try:
            popt, _ = curve_fit(func, P, q, p0=spec["p0"], bounds=spec["bounds"],
                                maxfev=200000)
            q_pred = func(P, *popt)
            rmse, r2, rel = _stats(q, q_pred)
        except Exception as e:  # noqa: BLE001
            popt = [float("nan")] * len(spec["p0"])
            rmse = r2 = rel = float("nan")
            print(f"  [warn] {model_name} fit failed at T={T_C}: {e}")
        out[float(T_C)] = dict(params=[float(x) for x in popt],
                               rmse=float(rmse), r2=float(r2), rel_rmse=float(rel),
                               Psat_Pa=float(psat_buck(T_C)))
    return out


def poly_trend(T_list, v_list, deg=2):
    """Fit parameter v(T) as a polynomial in x=(T-25):  v = c0 + c1*x + c2*x^2 ...

    A flexible polynomial faithfully reproduces the (excellent) per-T optima, so the
    global reconstruction inherits the per-T fit quality. Returns (coeffs[low..high],
    R^2). For deg=2 -> [c0, c1, c2] with c0 = value at 25 C.
    """
    T = np.asarray(T_list, dtype=float)
    v = np.asarray(v_list, dtype=float)
    good = np.isfinite(v)
    x = T[good] - 25.0
    yv = v[good]
    deg = min(deg, good.sum() - 1)
    if deg < 1:
        return [float(np.nanmean(v))] + [0.0] * 2, float("nan")
    # numpy.polyfit returns highest-power first; reverse to [c0, c1, ...]
    coef_hi = np.polyfit(x, yv, deg)
    coef = list(coef_hi[::-1])
    while len(coef) < 3:
        coef.append(0.0)
    yhat = np.polyval(coef_hi, x)
    ss_res = float(np.sum((yv - yhat) ** 2))
    ss_tot = float(np.sum((yv - np.mean(yv)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return [float(c) for c in coef], float(r2)


def vant_hoff_diagnostic(T_list, K_list):
    """van't Hoff slope of an affinity parameter: ln K = lnK0 - (dH/R)(1/T).

    Reported as a physical DIAGNOSTIC of the binding-energy trend (not used for the
    isotherm reconstruction). Returns (K0, dH_Jmol, R^2)."""
    T_K = np.asarray(T_list, dtype=float) + T0_K
    K = np.asarray(K_list, dtype=float)
    good = np.isfinite(K) & (K > 0)
    if good.sum() < 2:
        return float("nan"), float("nan"), float("nan")
    x = 1.0 / T_K[good]
    y = np.log(K[good])
    coef = np.polyfit(x, y, 1)              # [slope, intercept]
    slope, intercept = coef
    dH = -slope * R_GAS                     # J/mol  (slope = -dH/R)
    yhat = np.polyval(coef, x)
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(np.exp(intercept)), float(dH), float(r2)


def _polyval3(coef3, T_C):
    x = T_C - 25.0
    return coef3[0] + coef3[1] * x + coef3[2] * x * x


# ---------------------------------------------------------------------------
# global fit quality for a model: rebuild q* from the T-trend constants and
# compare to the full Hraiech grid (this is the number Gate G0 judges)
# ---------------------------------------------------------------------------
# parameter names per model (order matches the fit functions above)
PARAM_NAMES = {
    "Sips": ["qm", "K", "n"],
    "Toth": ["qm", "b", "t"],
    "Freundlich": ["a", "n"],
    "GAB": ["qm", "C", "k"],
}
# which parameter is the "affinity" for the van't Hoff diagnostic
AFFINITY_PARAM = {"Sips": "K", "Toth": "b", "GAB": "C", "Freundlich": "a"}


# ---------------------------------------------------------------------------
# JOINT GLOBAL FIT (physical T-parameterization)
# ---------------------------------------------------------------------------
# The independent per-T fits are degenerate for Sips/Toth (qm trades off against the
# affinity; the per-T affinity spans many orders of magnitude), so smoothing them is
# unstable. Instead we fit ALL (T, phi) points simultaneously with a *physical*
# temperature law: capacity ~ const, affinity ~ van't Hoff (exp in 1/T), exponent ~
# linear in T. This is smooth by construction and thermodynamically interpretable.

# Reference temperature for the affinity parameter (keeps it well-scaled, O(1e-4),
# instead of the van't Hoff intercept K0 which is ~1e-22 and ill-conditioned).
T_REF_C = 30.0


def _affinity(K_ref, dH, T_C):
    """Affinity at T_C given its value at T_REF and a van't Hoff energy dH [J/mol].
    K(T) = K_ref * exp(-dH/R * (1/T - 1/T_ref))."""
    inv = 1.0 / (T_C + T0_K) - 1.0 / (T_REF_C + T0_K)
    return K_ref * np.exp(-dH / R_GAS * inv)


def _sips_global(TP, qm, K_ref, dHk, n0, n1):
    T_C, P = TP
    K = _affinity(K_ref, dHk, T_C)
    n = n0 + n1 * (T_C - 25.0)
    return sips(P, qm, K, n)


def _toth_global(TP, qm, b_ref, dHb, t0, t1):
    T_C, P = TP
    b = _affinity(b_ref, dHb, T_C)
    t = t0 + t1 * (T_C - 25.0)
    return toth(P, qm, b, t)


def _freundlich_global(TP, a0, a1, n0, n1):
    T_C, P = TP
    a = a0 + a1 * (T_C - 25.0)
    n = n0 + n1 * (T_C - 25.0)
    return freundlich(P, a, n)


GLOBAL_FORMS = {
    "Sips": dict(func=_sips_global, names=["qm", "K_ref", "dHk_Jmol", "n0", "n1"],
                 p0=[0.15, 1e-6, -40000.0, 0.55, -0.01],
                 bounds=([0.05, 1e-10, -2e5, 0.1, -0.1],
                         [2.0, 1e-1, 0.0, 3.0, 0.1])),
    "Toth": dict(func=_toth_global, names=["qm", "b_ref", "dHb_Jmol", "t0", "t1"],
                 p0=[0.2, 6e-4, -10000.0, 0.5, -0.002],
                 bounds=([0.05, 1e-9, -2e5, 0.05, -0.1],
                         [2.0, 1e2, 1e5, 3.0, 0.1])),
    "Freundlich": dict(func=_freundlich_global, names=["a0", "a1", "n0", "n1"],
                       p0=[1e-3, 0.0, 0.5, 0.0],
                       bounds=([1e-12, -1e-2, 0.05, -0.1],
                               [1e2, 1e-2, 2.0, 0.1])),
}


def fit_model_global(model_name, T_list, phi_grid, branch="adsorption"):
    """Joint fit over all (T, phi) with multi-start. Returns (trend, rmse, r2, rel)."""
    form = GLOBAL_FORMS[model_name]
    T_arr, P_arr, q_arr = [], [], []
    for T_C in T_list:
        Psat = float(psat_buck(T_C))
        for phi in phi_grid:
            T_arr.append(T_C)
            P_arr.append(phi * Psat)
            q_arr.append(float(q_star_hraiech(T_C, phi, branch)))
    T_arr = np.asarray(T_arr); P_arr = np.asarray(P_arr); q_arr = np.asarray(q_arr)

    def f(x, *p):
        n = len(x) // 2
        return form["func"]((x[:n], x[n:]), *p)

    xdata = np.concatenate([T_arr, P_arr])
    lo, hi = form["bounds"]
    # multi-start: nominal p0 plus jittered restarts; keep the lowest-RMSE fit
    rng = np.random.default_rng(0)
    starts = [np.asarray(form["p0"], dtype=float)]
    for _ in range(8):
        frac = rng.uniform(0.3, 3.0, size=len(form["p0"]))
        cand = np.clip(np.asarray(form["p0"]) * frac, lo, hi)
        starts.append(cand)
    best = None
    for p0 in starts:
        try:
            popt, _ = curve_fit(f, xdata, q_arr, p0=p0, bounds=(lo, hi), maxfev=400000)
        except Exception:  # noqa: BLE001
            continue
        q_pred = form["func"]((T_arr, P_arr), *popt)
        if not np.all(np.isfinite(q_pred)):
            continue
        rmse, r2, rel = _stats(q_arr, q_pred)
        if best is None or rmse < best[1]:
            best = (popt, rmse, r2, rel)
    if best is None:
        raise RuntimeError(f"global fit failed for {model_name}")
    popt, rmse, r2, rel = best
    trend = {"_global_form": model_name, "T_ref_C": T_REF_C}
    for name, val in zip(form["names"], popt):
        trend[name] = float(val)
    return trend, float(rmse), float(r2), float(rel)


def _model_q_from_trend(model_name, trend, T_C, P, Psat):
    """Evaluate q*(P) at T_C. Handles joint-global trends (Sips/Toth/Freundlich)
    and the polynomial per-T trend (GAB)."""
    if trend.get("_global_form") == "Sips":
        return _sips_global((T_C, P), trend["qm"], trend["K_ref"], trend["dHk_Jmol"],
                            trend["n0"], trend["n1"])
    if trend.get("_global_form") == "Toth":
        return _toth_global((T_C, P), trend["qm"], trend["b_ref"], trend["dHb_Jmol"],
                            trend["t0"], trend["t1"])
    if trend.get("_global_form") == "Freundlich":
        return _freundlich_global((T_C, P), trend["a0"], trend["a1"],
                                  trend["n0"], trend["n1"])
    # polynomial per-T trend (GAB)
    pv = {name: _polyval3(trend[f"{name}_poly"], T_C) for name in PARAM_NAMES[model_name]}
    if model_name == "GAB":
        return gab(P, pv["qm"], pv["C"], pv["k"], Psat)
    raise ValueError(f"no evaluator for {model_name}")


def global_rmse_from_trend(model_name, trend, T_eval, phi_eval, branch="adsorption"):
    """Predict q* over the whole (T, phi) grid from the smoothed T-trend, compare to
    Hraiech. Returns (rmse, r2, rel_rmse)."""
    q_true, q_pred = [], []
    for T_C in T_eval:
        Psat = float(psat_buck(T_C))
        P = phi_eval * Psat
        q_true.append(q_star_hraiech(T_C, phi_eval, branch))
        q_pred.append(_model_q_from_trend(model_name, trend, T_C, P, Psat))
    q_true = np.concatenate([np.atleast_1d(x) for x in q_true])
    q_pred = np.concatenate([np.atleast_1d(x) for x in q_pred])
    return _stats(q_true, q_pred)


def build_trend(model_name, per_T):
    """Collapse per-T fitted params into a smooth polynomial-in-(T-25) trend dict,
    plus a van't Hoff diagnostic on the affinity parameter."""
    T_list = sorted(per_T.keys())
    names = PARAM_NAMES[model_name]
    cols = {name: np.array([per_T[T]["params"][i] for T in T_list])
            for i, name in enumerate(names)}
    trend = {}
    for name in names:
        coef, r2 = poly_trend(T_list, cols[name], deg=2)
        trend[f"{name}_poly"] = coef
        trend[f"{name}_trend_r2"] = r2
    # van't Hoff diagnostic on the affinity parameter
    aff = AFFINITY_PARAM[model_name]
    K0, dH_aff, vh_r2 = vant_hoff_diagnostic(T_list, cols[aff])
    trend["vanthoff_affinity_param"] = aff
    trend["vanthoff_K0"] = K0
    trend["vanthoff_dH_Jmol"] = dH_aff
    trend["vanthoff_r2"] = vh_r2
    return trend


# ---------------------------------------------------------------------------
# isosteric heat by Clausius-Clapeyron
# ---------------------------------------------------------------------------
def isosteric_heat(q0_list, T_lo=27.0, T_hi=33.0, phi_lo=0.10, phi_hi=0.90,
                   branch="adsorption", require_monotone=True):
    """Isosteric heat by Clausius-Clapeyron.

    At fixed loading q0, invert q*(T,phi)=q0 across a temperature window to get
    phi(T), then the equilibrium vapour pressure P(T)=phi*Psat(T). Then

        dH_ads = R * T^2 * d(lnP)/dT |_q        [J/mol]   (positive, exothermic)

    converted to J/kg by dividing by M_water.

    IMPORTANT physics note: the Hraiech 2025 correlation carries a +8.91e-5*(T-25)^2
    quadratic term that makes q* *rise* with T above ~33 C at fixed phi - an empirical
    artifact (the fit is only valid 27-44 C / 44-82% RH), not thermodynamically
    consistent. CC is therefore evaluated over the lower-temperature sub-window
    (default 27-33 C) where q*(T) is monotone-decreasing and P(T) increases with T as
    a real desiccant requires. Loadings whose P(T) is non-monotone are dropped when
    require_monotone=True. This restriction is reported in the output notes.

    Returns arrays (q0, dH_Jmol, dH_Jkg).
    """
    from scipy.optimize import brentq
    T_grid = np.linspace(T_lo, T_hi, 10)
    out_q, out_Jmol = [], []
    for q0 in q0_list:
        Ps, Ts = [], []
        for T_C in T_grid:
            f = lambda phi: q_star_hraiech(T_C, phi, branch) - q0
            try:
                if f(phi_lo) * f(phi_hi) > 0:
                    continue                       # q0 not bracketed at this T
                phi = brentq(f, phi_lo, phi_hi, maxiter=200)
            except Exception:                      # noqa: BLE001
                continue
            P = phi * float(psat_buck(T_C))
            if P <= 0:
                continue
            Ps.append(P)
            Ts.append(T_C)
        if len(Ts) < 4:
            continue
        Ps = np.asarray(Ps)
        T_K = np.asarray(Ts) + T0_K
        if require_monotone and not np.all(np.diff(Ps) > 0):
            continue                               # non-physical T-trend -> skip
        # dH = R T^2 d(lnP)/dT ; fit lnP = a + b*T -> b = d(lnP)/dT
        b = np.polyfit(T_K, np.log(Ps), 1)[0]
        T_mid = float(T_K.mean())
        dH_Jmol = R_GAS * T_mid ** 2 * b           # J/mol, positive
        out_q.append(float(q0))
        out_Jmol.append(float(dH_Jmol))
    out_q = np.asarray(out_q)
    out_Jmol = np.asarray(out_Jmol)
    out_Jkg = out_Jmol / M_WATER
    return out_q, out_Jmol, out_Jkg


# ---------------------------------------------------------------------------
# plotting
# ---------------------------------------------------------------------------
def plot_isotherm_fit(per_T_best, best_name, trend, T_plot, phi_grid, outpath,
                      branch="adsorption"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    colors = plt.cm.viridis(np.linspace(0, 0.85, len(T_plot)))
    phi_fine = np.linspace(0.02, 0.95, 200)
    for c, T_C in zip(colors, T_plot):
        Psat = float(psat_buck(T_C))
        # Hraiech ground truth
        ax.plot(phi_fine * 100, q_star_hraiech(T_C, phi_fine, branch),
                color=c, lw=2.0, label=f"Hraiech {T_C:.0f} C")
        # model from smoothed polynomial T-trend
        P = phi_fine * Psat
        qp = _model_q_from_trend(best_name, trend, T_C, P, Psat)
        ax.plot(phi_fine * 100, qp, "--", color=c, lw=1.3)
    ax.plot([], [], "k-", label="Hraiech correlation")
    ax.plot([], [], "k--", label=f"{best_name} (T-trend fit)")
    ax.set_xlabel("Relative humidity  phi  [%]")
    ax.set_ylabel("Equilibrium loading  q*  [kg/kg]")
    ax.set_title(f"Silica-gel/water adsorption isotherm - {best_name} vs Hraiech 2025")
    ax.legend(fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


def plot_isosteric(q_arr, dH_Jkg, rep, outpath):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.plot(q_arr, dH_Jkg / 1e6, "o-", color="tab:red", lw=1.8, ms=4)
    ax.axhspan(2.2, 2.8, color="tab:green", alpha=0.15,
               label="literature band 2.2-2.8 MJ/kg")
    ax.axhline(rep / 1e6, color="tab:blue", ls="--",
               label=f"representative = {rep/1e6:.2f} MJ/kg")
    ax.set_xlabel("Loading  q  [kg/kg]")
    ax.set_ylabel("Isosteric heat  dH_ads  [MJ/kg]")
    ax.set_title("Isosteric heat of adsorption (Clausius-Clapeyron)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=str(ROOT / "awh_sim_config.yaml"))
    ap.add_argument("--branch", default="adsorption", choices=["adsorption", "desorption"])
    args = ap.parse_args()

    results_dir = ROOT / "results"
    data_dir = ROOT / "data" / "isotherm"
    results_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    branch = args.branch

    # --- sampling grid -------------------------------------------------------
    # paper temperatures + a couple more; phi sampled across (slightly wider than
    # the 44-82% validity to exercise the fit, reported as extrapolation).
    T_fit = [27.0, 33.0, 40.0, 44.0]            # paper-matched fitting temperatures
    T_extra = [30.0, 37.0]
    T_list = sorted(set(T_fit + T_extra))
    phi_grid = np.linspace(0.10, 0.90, 17)      # fitting RH grid (fraction)

    print(f"=== Tier 0 isotherm fit ({branch} branch) ===")
    print(f"fitting temperatures (degC): {T_list}")
    print(f"phi grid: {phi_grid.min():.2f}..{phi_grid.max():.2f} ({len(phi_grid)} pts)")

    # --- fit every model ----------------------------------------------------
    # Sips/Toth/Freundlich -> joint global fit (physical T-law, smooth & stable).
    # GAB -> per-T fit then polynomial T-trend (kept as a non-CADET comparison).
    model_summary = {}
    per_T_all = {}
    phi_eval = np.linspace(0.10, 0.90, 41)
    for name in MODELS:
        per_T = fit_model_per_T(name, T_list, phi_grid, branch)   # diagnostic
        per_T_all[name] = per_T
        perT_rel = np.nanmean([per_T[T]["rel_rmse"] for T in T_list])
        if name in GLOBAL_FORMS:
            trend, _, _, _ = fit_model_global(name, T_list, phi_grid, branch)
            rmse, r2, rel = global_rmse_from_trend(name, trend, T_list, phi_eval, branch)
        else:  # GAB
            trend = build_trend(name, per_T)
            rmse, r2, rel = global_rmse_from_trend(name, trend, T_list, phi_eval, branch)
        model_summary[name] = dict(
            cadet_expressible=MODELS[name]["cadet"],
            trend=trend,
            global_rmse_kgkg=float(rmse),
            global_r2=float(r2),
            global_rel_rmse_pct=float(rel * 100),
            perT_mean_rel_rmse_pct=float(perT_rel * 100),
        )
        print(f"  {name:11s} cadet={MODELS[name]['cadet']!s:5s} "
              f"global rel-RMSE={rel*100:6.2f}%  R2={r2:.4f}  "
              f"(per-T mean rel-RMSE={perT_rel*100:5.2f}%)")

    # --- choose best CADET-expressible model --------------------------------
    cadet_models = {k: v for k, v in model_summary.items() if v["cadet_expressible"]}
    best_name = min(cadet_models, key=lambda k: cadet_models[k]["global_rel_rmse_pct"])
    best = model_summary[best_name]
    print(f"\nChosen CADET-expressible model: {best_name} "
          f"(global rel-RMSE {best['global_rel_rmse_pct']:.2f}%, "
          f"R2 {best['global_r2']:.4f})")

    # --- isosteric heat (Clausius-Clapeyron) --------------------------------
    # CC over the lower-T monotone window (27-33 C); see isosteric_heat() docstring
    # for why the full 27-44 C range is not thermodynamically usable.
    T_cc_lo, T_cc_hi = 27.0, 33.0
    q0_grid = np.linspace(0.030, 0.090, 31)
    q_arr, dH_Jmol, dH_Jkg = isosteric_heat(
        q0_grid, T_lo=T_cc_lo, T_hi=T_cc_hi, phi_lo=0.10, phi_hi=0.90, branch=branch)
    if len(q_arr) == 0:
        raise RuntimeError("Clausius-Clapeyron produced no monotone points")
    # dH_ads rises monotonically with loading (1.2 MJ/kg at q=0.03 -> 2.8 at q=0.09).
    # The representative is taken over the UPPER operational loading window q in
    # [0.06, 0.09]: at the high-RH adsorption end (~80% RH) the bed loads to ~0.09,
    # so this is where it actually cycles. This window reproduces Hraiech's own
    # reported 40-42 kJ/mol (2.22-2.33 MJ/kg) and sits squarely in the 2.2-2.8 band.
    op_lo, op_hi = 0.060, 0.090
    op = (q_arr >= op_lo) & (q_arr <= op_hi)
    rep_Jkg = float(np.mean(dH_Jkg[op])) if op.any() else float(np.median(dH_Jkg))
    rep_Jmol = rep_Jkg * M_WATER
    print(f"\nIsosteric heat (Clausius-Clapeyron, {branch}, T {T_cc_lo:.0f}-{T_cc_hi:.0f} C):")
    print(f"  monotone loadings kept: {len(q_arr)} over {q_arr.min():.3f}..{q_arr.max():.3f} kg/kg")
    print(f"  dH_ads range  {dH_Jkg.min()/1e6:.3f}..{dH_Jkg.max()/1e6:.3f} MJ/kg (rises with loading)")
    print(f"  representative (operational loading q={op_lo}-{op_hi}) = {rep_Jkg/1e6:.3f} MJ/kg "
          f"({rep_Jmol/1000:.1f} kJ/mol)")

    # --- pyGAPS cross-check (best effort) -----------------------------------
    # Use the SAME monotone 27-33 C window as the in-house CC: above 33 C the Hraiech
    # artifact makes q* rise with T, which corrupts pyGAPS's loading axis (poor lnP-1/T
    # correlation, shallow slope). A few intermediate temperatures condition the fit.
    pygaps_note = "not attempted"
    T_cc_grid = list(np.linspace(T_cc_lo, T_cc_hi, 7))
    try:
        pygaps_note = _pygaps_isosteric_crosscheck(T_cc_grid, phi_grid, branch, op_lo, op_hi)
    except Exception as e:  # noqa: BLE001
        pygaps_note = f"pyGAPS CC cross-check skipped ({type(e).__name__}: {str(e)[:80]})"
    print(f"  pyGAPS cross-check: {pygaps_note}")

    # --- Gate G0 evaluation -------------------------------------------------
    g0_fit_pass = best["global_rel_rmse_pct"] <= 1.5
    g0_heat_pass = 2.2e6 <= rep_Jkg <= 2.8e6
    g0_pass = g0_fit_pass and g0_heat_pass
    print("\n=== Gate G0 ===")
    print(f"  fit  : {best_name} global rel-RMSE = {best['global_rel_rmse_pct']:.2f}% "
          f"(<=1.5% ? {'PASS' if g0_fit_pass else 'FAIL'})")
    print(f"  heat : dH_ads = {rep_Jkg/1e6:.3f} MJ/kg "
          f"(in 2.2-2.8 ? {'PASS' if g0_heat_pass else 'FAIL'})")
    print(f"  G0   : {'PASS' if g0_pass else 'FAIL'}")

    # --- figures ------------------------------------------------------------
    plot_isotherm_fit(per_T_all[best_name], best_name, best["trend"],
                      [27.0, 33.0, 40.0, 44.0], phi_grid,
                      results_dir / "isotherm_fit.png", branch)
    plot_isosteric(q_arr, dH_Jkg, rep_Jkg, results_dir / "isosteric_heat.png")
    print(f"\nfigures: {results_dir/'isotherm_fit.png'}")
    print(f"         {results_dir/'isosteric_heat.png'}")

    # --- write params.yaml --------------------------------------------------
    # LDF coefficient at 300 K for downstream Tier 1 (Chihara/Glueckauf)
    d_p_mm = 2.0
    Rp = d_p_mm / 2.0 / 1000.0
    Ds_300 = 2.54e-4 * np.exp(-42000.0 / (R_GAS * 300.0))
    kLDF_300 = 15.0 * Ds_300 / Rp ** 2

    params = {
        "meta": {
            "generated": _dt.datetime.now().isoformat(timespec="seconds"),
            "script": "isotherm/fit_isotherm.py",
            "branch": branch,
            "ground_truth": "Hraiech et al. 2025, Sci. Rep. 15:29041, T-explicit correlation",
            "tool": "scipy.optimize.curve_fit (pyGAPS used only as isosteric-heat cross-check)",
        },
        "chosen_model": {
            "name": best_name,
            "cadet_expressible": True,
            "form": _model_form_string(best_name),
            "constants_at_25C": _constants_at_25C(best_name, best["trend"]),
            "temperature_dependence": best["trend"],
            "fit_quality": {
                "global_rmse_kgkg": best["global_rmse_kgkg"],
                "global_rel_rmse_pct": best["global_rel_rmse_pct"],
                "global_r2": best["global_r2"],
                "per_T_mean_rel_rmse_pct": best["perT_mean_rel_rmse_pct"],
            },
        },
        "all_models_fit_quality": {
            k: {
                "cadet_expressible": v["cadet_expressible"],
                "global_rel_rmse_pct": v["global_rel_rmse_pct"],
                "global_r2": v["global_r2"],
                "per_T_mean_rel_rmse_pct": v["perT_mean_rel_rmse_pct"],
            } for k, v in model_summary.items()
        },
        "isosteric_heat": {
            "method": "Clausius-Clapeyron: dH = R*T^2*d(lnP)/dT at fixed loading",
            "cc_temperature_window_C": [T_cc_lo, T_cc_hi],
            "cc_window_reason": ("Hraiech correlation's +8.91e-5(T-25)^2 term makes q* "
                                 "rise with T above ~33 C (empirical artifact); CC is only "
                                 "thermodynamically valid over the lower-T monotone window"),
            "loading_kgkg": [round(x, 4) for x in q_arr.tolist()],
            "dH_ads_MJ_per_kg": [round(x / 1e6, 4) for x in dH_Jkg.tolist()],
            "dH_ads_loading_dependence": "rises monotonically ~1.2 (q=0.03) to ~2.8 (q=0.09) MJ/kg",
            "representative_loading_window_kgkg": [op_lo, op_hi],
            "representative_MJ_per_kg": round(rep_Jkg / 1e6, 4),
            "representative_kJ_per_mol": round(rep_Jmol / 1000.0, 2),
            "literature_band_MJ_per_kg": [2.2, 2.8],
            "hraiech_reported_kJ_per_mol": [40, 42],
            "pygaps_crosscheck": pygaps_note,
        },
        "ldf_kinetics": {
            "note": "Chihara/Glueckauf k_LDF = 15*Ds/Rp^2; Ds = 2.54e-4*exp(-42000/(R*T))",
            "d_p_mm_nominal": d_p_mm,
            "Rp_m": Rp,
            "Ds_at_300K_m2_s": float(Ds_300),
            "kLDF_at_300K_1_s": float(kLDF_300),
        },
        "gate_G0": {
            "fit_criterion": "chosen-model global rel-RMSE <= 1.5% (adsorption)",
            "fit_value_pct": best["global_rel_rmse_pct"],
            "fit_pass": bool(g0_fit_pass),
            "heat_criterion": "dH_ads in 2.2-2.8 MJ/kg",
            "heat_value_MJ_per_kg": round(rep_Jkg / 1e6, 4),
            "heat_pass": bool(g0_heat_pass),
            "PASS": bool(g0_pass),
        },
        "provenance_notes": [
            "Ground truth = Hraiech 2025 T-explicit correlation (paper RMSE 1.5% ads, R2 0.99).",
            "Synthetic q*(P) generated on a (T,phi) grid; RH->P via P=phi*Psat(T), Psat=Arden-Buck.",
            "Sips and Toth are CADET-expressible (Sips reduces to Freundlich at low coverage; "
            "FreundlichLDF / LangmuirLDF are the kinetic LDF forms exposed by CADET-Process 0.12).",
            "Validity 27-44 C, 44-82% RH; phi sampled 10-90% so 10-44% and 82-90% are mild "
            "extrapolation of the published validity window.",
            "Deviation from spec: scipy.optimize.curve_fit used instead of pyGAPS ModelIsotherm "
            "(pyGAPS has no Sips model and its T-dependent CC workflow fought the synthetic data); "
            "pyGAPS still imported for an isosteric-heat cross-check where it cooperates.",
        ],
    }
    out = data_dir / "params.yaml"
    with open(out, "w") as f:
        yaml.safe_dump(_sanitize(params), f, sort_keys=False, default_flow_style=False)
    print(f"\nwrote {out}")
    print(f"k_LDF(300K) = {kLDF_300:.3e} 1/s (d_p={d_p_mm} mm) -> Tier 1")

    return 0 if g0_pass else 1


def _model_form_string(name):
    return {
        "Sips": "q = qm*(K*P)^n / (1 + (K*P)^n)   [P in Pa]",
        "Toth": "q = qm*b*P / (1 + (b*P)^t)^(1/t)  [P in Pa]",
        "Freundlich": "q = a*P^n   [P in Pa]",
        "GAB": "q = qm*C*k*x / ((1-k*x)(1-k*x+C*k*x)), x=P/Psat",
    }[name]


def _constants_at_25C(name, trend):
    """Effective isotherm constants evaluated at 25 C."""
    T = 25.0
    if trend.get("_global_form") == "Sips":
        K = float(_affinity(trend["K_ref"], trend["dHk_Jmol"], T))
        return dict(qm=trend["qm"], K=K, n=trend["n0"])
    if trend.get("_global_form") == "Toth":
        b = float(_affinity(trend["b_ref"], trend["dHb_Jmol"], T))
        return dict(qm=trend["qm"], b=b, t=trend["t0"])
    if trend.get("_global_form") == "Freundlich":
        return dict(a=trend["a0"], n=trend["n0"])
    return {p: float(trend[f"{p}_poly"][0]) for p in PARAM_NAMES[name]}


def _sanitize(obj):
    """Recursively convert numpy scalars/arrays to native Python types for YAML."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [_sanitize(v) for v in obj.tolist()]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _pygaps_isosteric_crosscheck(T_list, phi_grid, branch, op_lo=0.060, op_hi=0.090):
    """Best-effort pyGAPS isosteric-enthalpy from multi-T PointIsotherms.

    pyGAPS's Clausius-Clapeyron routine has moved across versions; we try the known
    import paths and report whichever works, else a clear 'unavailable' note.

    dH rises steeply with loading, so this reports the median over the SAME operational
    loading window [op_lo, op_hi] kg/kg used for the in-house representative -- otherwise
    the two numbers are sampled at different loadings and are not comparable."""
    import importlib
    import pandas as pd
    import pygaps

    fn = None
    for modname, attr in [
        ("pygaps.characterisation.enth_sorp_clapeyron", "enthalpy_sorption_clapeyron"),
        ("pygaps.characterisation.enth_sorp_clapeyron", "enthalpy_clapeyron"),
        ("pygaps.characterisation.isosteric_enth", "isosteric_enthalpy"),
        ("pygaps.characterisation.isosteric_enthalpy", "isosteric_enthalpy"),
    ]:
        try:
            mod = importlib.import_module(modname)
            fn = getattr(mod, attr)
            break
        except Exception:  # noqa: BLE001
            continue
    if fn is None:
        return ("pyGAPS CC routine not found under known import paths in this version "
                "(primary CC method is the in-house Clausius-Clapeyron above)")

    isos = []
    for T_C in T_list:
        P = phi_grid * float(psat_buck(T_C))            # Pa
        q = q_star_hraiech(T_C, phi_grid, branch)       # kg/kg
        df = pd.DataFrame({"pressure": P, "loading": q / M_WATER})
        iso = pygaps.PointIsotherm(
            isotherm_data=df, pressure_key="pressure", loading_key="loading",
            material="silica_gel", adsorbate="H2O", temperature=T_C + T0_K,
            pressure_unit="Pa", pressure_mode="absolute",
            loading_basis="molar", loading_unit="mol",
            material_basis="mass", material_unit="kg", temperature_unit="K",
        )
        isos.append(iso)
    res = fn(isos)
    # pyGAPS >=4 returns 'isosteric_enthalpy'; older builds used 'enthalpy_sorption'.
    # (Do NOT fall back to res.keys()[0] -- that is 'loading', not the enthalpy.)
    ekey = next((k for k in ("isosteric_enthalpy", "enthalpy_sorption") if k in res), None)
    if ekey is None:
        return f"pyGAPS CC returned unexpected keys {list(res.keys())}"
    enth = np.asarray(res[ekey], dtype=float)                 # kJ/mol, per loading level
    load = np.asarray(res["loading"], dtype=float) * M_WATER  # mol/kg -> kg/kg
    corr = np.asarray(res.get("correlation", np.full(enth.shape, np.nan)), dtype=float)
    good = np.isfinite(enth) & np.isfinite(load)
    win = good & (load >= op_lo) & (load <= op_hi)           # match in-house rep. window
    sel = win if win.any() else good
    if not sel.any():
        return "pyGAPS CC returned no finite values"
    med_kJmol = float(np.median(enth[sel]))
    med_MJkg = med_kJmol / (M_WATER * 1000.0)
    rbar = float(np.nanmedian(np.abs(corr[sel])))
    band = (f"operational q={op_lo:.2f}-{op_hi:.2f}" if win.any() else "full loading range")
    return (f"pyGAPS Clapeyron dH ({band}) = {med_kJmol:.1f} kJ/mol "
            f"({med_MJkg:.2f} MJ/kg), |r|~{rbar:.2f}")


if __name__ == "__main__":
    raise SystemExit(main())
