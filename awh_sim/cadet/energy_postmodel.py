#!/usr/bin/env python3
"""Tier 1 - lumped energy post-model for CADET (cheap Q_reg / SEC estimate).

CADET-Core is isothermal, so regeneration energy and SEC are estimated post-hoc from
the CADET mass result + the prescribed T schedule:

    Q_reg ~ sensible bed heating   integral (rho c_p)_eff dT
            + desorption enthalpy   dH_ads * delta_q * m_gel
            + fan work              Ergun dP * volumetric flow * t
    SEC   = (Q_reg + fan energy) / m_w

These are the LOW-FIDELITY leg for Q_reg / SEC; OpenFOAM supplies the high-fidelity
truth and the MFK surrogate fuses them (docs/DESIGN_SPEC.md sec 3, sec 5).
"""
from __future__ import annotations


def ergun_dp(u_face, L_bed, d_p, eps, mu=1.8e-5, rho=1.2):
    """Ergun pressure drop [Pa].

    dP = 150*(1-e)^2/(e^3 dp^2) * mu*u*L  +  1.75*(1-e)/(e^3 dp) * rho*u^2*L

    Also used directly as the dP response (no surrogate). All SI units.
    """
    visc = 150.0 * (1.0 - eps) ** 2 / (eps ** 3 * d_p ** 2) * mu * u_face * L_bed
    inert = 1.75 * (1.0 - eps) / (eps ** 3 * d_p) * rho * u_face ** 2 * L_bed
    return visc + inert


def lumped_energy(result, params):
    """Lumped regeneration energy and SEC.

    `result` is a dict with at least:
        m_w_kg        harvested / adsorbed water mass per cycle [kg]
        m_gel_kg      dry silica-gel mass in the bed [kg]
        dq_kgkg       loading swing delta_q over the cycle [kg/kg]
        dT_reg_K      bed temperature rise for regeneration [K]
        u_face_m_s, L_bed_m, d_p_m, eps, t_cycle_s, area_m2  (for fan work)
    `params` is the Tier-0 params dict (for dH_ads).

    Returns dict with Q_sensible, Q_desorption, E_fan, Q_reg, SEC (all SI / per cycle).
    """
    cp_solid = params.get("bed", {}).get("cp_solid_J_kgK", 921.0)
    cp_w_ads = 4180.0
    dH_ads = params["isotherm"]["dH_ads_J_per_kg"]

    m_gel = result["m_gel_kg"]
    m_w = result["m_w_kg"]
    dq = result.get("dq_kgkg", m_w / m_gel if m_gel > 0 else 0.0)
    dT = result["dT_reg_K"]

    # sensible heating of gel + adsorbed water
    q_avg = result.get("q_avg_kgkg", dq)
    rho_cp_eff = cp_solid + q_avg * cp_w_ads          # J/kg-gel/K
    Q_sensible = m_gel * rho_cp_eff * dT              # J

    # desorption enthalpy
    Q_desorption = dH_ads * dq * m_gel               # J

    # fan work over the cycle (Ergun dP x volumetric flow x time)
    dP = ergun_dp(result["u_face_m_s"], result["L_bed_m"], result["d_p_m"], result["eps"])
    Q_vol = result["u_face_m_s"] * result["area_m2"]  # m3/s superficial
    E_fan = dP * Q_vol * result["t_cycle_s"]          # J

    Q_reg = Q_sensible + Q_desorption
    total = Q_reg + E_fan
    SEC_J_per_kg = total / m_w if m_w > 0 else float("inf")
    return {
        "Q_sensible_J": float(Q_sensible),
        "Q_desorption_J": float(Q_desorption),
        "E_fan_J": float(E_fan),
        "Q_reg_J": float(Q_reg),
        "dP_Pa": float(dP),
        "SEC_J_per_kg": float(SEC_J_per_kg),
        "SEC_kWh_per_kg": float(SEC_J_per_kg / 3.6e6),
    }
