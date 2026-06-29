"""
===================================================================
Script:      tec_robot_design.py
Author:      Graduation Project — Autonomous TEC PV-Cleaning Robot
Date:        2026-06-01
Purpose:     Complete, reproducible design + simulation engine for an
             autonomous photovoltaic-panel cleaning robot that harvests
             its own cleaning water from atmospheric moisture using
             thermoelectric (Peltier, TEC1-12706) cooling.

             Computes, from hourly Benban climate (NASA POWER, 2020):
               (1) Psychrometrics  : Buck P_sat, partial pressure, humidity
                                     ratio w, Magnus dew point  (per hour)
               (2) TEC condensation: coupled cold-plate / hot-side energy
                                     balance solved per hour for each tile
                                     -> condensate mass, COP, SEC
               (3) Sizing          : number of TEC1-12706 tiles for the
                                     0.5-1.0 L/day target
               (4) Energy budget   : TEC + fans + pump + drive + MCU,
                                     battery capacity, dedicated-PV size
               (5) Mechanics check : drive traction torque, hot-side heat
                                     sink thermal resistance requirement
             Produces verified numbers (printed + CSV/JSON) and
             IEEE/LaTeX-ready PDF figures.

Units:       SI throughout unless noted at I/O (temperatures in degC at I/O,
             converted to K inside thermodynamic relations).
References:  Buck 1981; Lawrence 2005 (Magnus); Incropera (Lewis analogy);
             FerroTec / TEC1-12706 datasheet; NASA POWER (power.larc.nasa.gov).
===================================================================
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Paths (resolve project root relative to this script so it is portable)
# ----------------------------------------------------------------------
HERE      = os.path.dirname(os.path.abspath(__file__))
ROOT      = os.path.abspath(os.path.join(HERE, os.pardir))
OUT_DIR   = os.path.join(ROOT, "output")
FIG_DIR   = os.path.join(ROOT, "figures")
HOURLY_CSV = os.path.join(OUT_DIR, "nasa_power_hourly.csv")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

# ======================================================================
#  PARAMETERS  (all constants here; no magic numbers in functions)
# ======================================================================

# ---- Physical constants -------------------------------------------------
R_UNIV  = 8.314          # [J/(mol K)] universal gas constant
M_W     = 0.018015       # [kg/mol]    molar mass of water
G       = 9.81           # [m/s^2]     gravity

# ---- Site (Benban Solar Park) ------------------------------------------
ELEV_M  = 180.0          # [m]  site elevation
# Barometric pressure at elevation (ISA): P = P0*(1 - 2.25577e-5 h)^5.2559
P_ATM_KPA = 101.325 * (1.0 - 2.25577e-5 * ELEV_M) ** 5.2559   # [kPa]

# ---- Moist-air properties (~25-30 degC film) ---------------------------
RHO_AIR = 1.15           # [kg/m^3]  density of air at ~40 degC
CP_A    = 1006.0         # [J/(kg K)] dry-air specific heat
CP_V    = 1860.0         # [J/(kg K)] water-vapour specific heat
K_AIR   = 0.026          # [W/(m K)]  air thermal conductivity
NU_AIR  = 1.6e-5         # [m^2/s]    air kinematic viscosity
PR_AIR  = 0.707          # [-]        Prandtl number
LE      = 0.845          # [-]        Lewis number (air-water)
LE_23   = LE ** (2.0/3.0)

# ---- TEC1-12706 Peltier module (datasheet, Th_ref = 27 degC = 300.15 K)-
# Selected Egyptian-market module: Micro Ohm Electronics, ~130 EGP (Apr 2026).
TEC_IMAX   = 6.0         # [A]  max current
TEC_UMAX   = 15.4        # [V]  max voltage
TEC_DTMAX  = 66.0        # [K]  max temperature difference (Th=27 degC)
TEC_THREF  = 300.15      # [K]  datasheet hot-side reference temperature
# Closed-form module coefficients from the four max parameters
# (standard derivation, e.g. Lineykin & Ben-Yaakov 2007):
TEC_ALPHA = TEC_UMAX / TEC_THREF                                   # [V/K]  Seebeck
TEC_R     = (TEC_UMAX / TEC_IMAX) * (TEC_THREF - TEC_DTMAX) / TEC_THREF   # [ohm]
TEC_K     = (TEC_UMAX * TEC_IMAX * (TEC_THREF - TEC_DTMAX)) / \
            (2.0 * TEC_THREF * TEC_DTMAX)                          # [W/K]  conductance
TEC_PRICE_EGP = 130.0    # [EGP] retail unit price (Apr 2026)
EGP_PER_USD   = 48.0     # [EGP/USD] exchange rate (Apr 2026)

# ---- Cold-side condenser heat exchanger (per tile) ---------------------
A_COLD     = 0.05        # [m^2] effective finned cold-side surface per tile
V_FACE     = 2.0         # [m/s] forced face velocity from cold-side fan
L_CHAR     = 0.05        # [m]   characteristic length of cold exchanger
DT_MARGIN  = 5.0         # [K]   plate sub-cooling below dew point (baseline)

# ---- Hot-side dissipation ----------------------------------------------
R_TH_HS    = 0.15        # [K/W] hot-side heat-sink thermal resistance per tile
                         # (aggressive forced convection, finned + fan)

# ---- Operating strategy -------------------------------------------------
NIGHT_START = 18         # operate TEC from 18:00 ...
NIGHT_END   = 6          # ... to 06:00 (cool, humid window) -> 12 h/day
TC_FROST_MIN = 1.0       # [degC] cold-plate floor to avoid frosting/icing

# ---- Robot / cleaning parameters ---------------------------------------
PANEL_AREA      = 2.0    # [m^2] one residential panel (1.0 x 2.0 m)
WATER_PER_M2    = 1.8    # [L/m^2] cleaning water per event (project_inputs)
WATER_PER_EVENT = WATER_PER_M2 * PANEL_AREA      # [L] per cleaning event
TARGET_LDAY_LO  = 0.5    # [L/day] design target (low)
TARGET_LDAY_HI  = 1.0    # [L/day] design target (high)

# ---- Parasitic / auxiliary electrical loads ----------------------------
P_FAN_EACH = 2.5         # [W] each small axial fan
P_MCU      = 1.5         # [W] microcontroller + sensor suite (continuous)
P_PUMP     = 18.0        # [W] cleaning-fluid pump (only during cleaning)
P_DRIVE    = 30.0        # [W] two drive motors total (only during cleaning)

# ---- Robot mechanics (for traction torque check) -----------------------
M_ROBOT    = 6.0         # [kg] estimated robot mass (chassis+tank+TEC stack)
MU_ROLL    = 0.15        # [-]  effective resistance (brush contact + rolling)
PANEL_TILT = 24.0        # [deg] panel tilt (~latitude)
R_WHEEL    = 0.03        # [m]  drive wheel radius
ETA_DRIVE  = 0.7         # [-]  drivetrain efficiency
V_CLEAN    = 0.05        # [m/s] cleaning traverse speed
BRUSH_W    = 0.25        # [m]  effective brush width
OVERLAP    = 0.10        # [-]  pass overlap

# ---- PV (dedicated robot panel) ----------------------------------------
PSH_BENBAN = 5.8         # [kWh/m^2/day] ~peak sun hours (annual mean GHI)
PR_PV      = 0.80        # [-] performance ratio
ETA_PV_MOD = 0.215       # [-] module efficiency (STC)

# ---- Battery ------------------------------------------------------------
V_BATT     = 12.0        # [V]  nominal bus voltage
DOD        = 0.80        # [-]  Li-ion depth of discharge
ETA_CHG    = 0.95        # [-]  charge efficiency
BATT_MARGIN = 1.20       # [-]  20% design margin

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# ======================================================================
#  PSYCHROMETRIC FUNCTIONS
# ======================================================================

def p_sat_buck(T_C):
    """Saturation vapour pressure (Buck 1981) [kPa]. T_C in degC."""
    return 0.61121 * np.exp((18.678 - T_C/234.5) * T_C / (257.14 + T_C))

def dew_point_magnus(T_C, RH):
    """Magnus/Lawrence(2005) dew point [degC]. T_C degC, RH percent."""
    a, b = 17.625, 243.04
    RH = np.clip(RH, 1e-3, 100.0)
    alpha = np.log(RH/100.0) + a*T_C/(b + T_C)
    return b*alpha / (a - alpha)

def humidity_ratio(T_C, RH):
    """Humidity ratio w [kg_w/kg_dryair]. Uses site P_atm."""
    Pv = (RH/100.0) * p_sat_buck(T_C)
    return 0.622 * Pv / (P_ATM_KPA - Pv)

def vapour_density(P_kPa, T_C):
    """Vapour density from partial pressure [kg/m^3]. Ideal gas."""
    return (P_kPa*1000.0) * M_W / (R_UNIV * (T_C + 273.15))

def h_fg(T_C):
    """Latent heat of vaporisation [J/kg]. Linear fit, T_C in degC."""
    return (2500.0 - 2.35*T_C) * 1000.0

# ======================================================================
#  CONVECTION / MASS TRANSFER ON COLD EXCHANGER
# ======================================================================

def h_conv_forced():
    """Forced-convection coeff on cold exchanger [W/(m^2 K)] (flat-plate Nu)."""
    Re = V_FACE * L_CHAR / NU_AIR
    if Re < 5e5:
        Nu = 0.664 * Re**0.5 * PR_AIR**(1.0/3.0)        # laminar
    else:
        Nu = (0.037*Re**0.8 - 871.0) * PR_AIR**(1.0/3.0) # turbulent
    return Nu * K_AIR / L_CHAR

H_CONV = h_conv_forced()   # constant for fixed airflow/geometry

def h_mass():
    """Mass-transfer coeff [m/s] via Lewis analogy."""
    cp_m = CP_A  # dry-air basis adequate (w small)
    return H_CONV / (RHO_AIR * cp_m * LE_23)

H_MASS = h_mass()

# ======================================================================
#  COUPLED TEC OPERATING POINT (per tile, per hour)
# ======================================================================

def _cold_loads(T_amb, rho_v_air, T_c):
    """Cold-side loads at plate temperature T_c [degC].
    Returns (mdot[kg/s], Qc_load[W]) for ONE tile."""
    rho_v_s = vapour_density(p_sat_buck(T_c), T_c)
    drho = max(rho_v_air - rho_v_s, 0.0)
    mdot = H_MASS * A_COLD * drho                  # [kg/s]
    Q_lat = mdot * h_fg(T_c)
    Q_sens = H_CONV * A_COLD * max(T_amb - T_c, 0.0)
    return mdot, Q_sens + Q_lat

def tec_tile_operating_point(T_amb, RH, dt_margin=DT_MARGIN):
    """
    Solve the coupled cold-plate / hot-side energy balance for ONE TEC1-12706.

    Control logic:
      * Target plate temperature  T_c* = max(T_dew - margin, frost floor).
      * Mode 'A' (setpoint held): a current I <= Imax delivers the load at
        T_c* -> efficient operation.
      * Mode 'B' (capacity limited): even at Imax the plate cannot reach T_c*;
        the plate floats up to the equilibrium temperature where the TEC cold
        capacity equals the cold load (solved by bisection). Less water.
      * Mode 'off': air drier than the saturated plate, or no sub-cooling
        possible -> no condensation.

    Returns dict: mode, mdot[kg/s], W[W], COP, Qc[W], Tc[degC], Th[degC], I[A].
    """
    T_dew = dew_point_magnus(T_amb, RH)
    Tc_target = max(T_dew - dt_margin, TC_FROST_MIN)   # frost-protected target
    OFF = dict(mode='off', mdot=0.0, W=0.0, COP=0.0, Qc=0.0,
               Tc=Tc_target, Th=T_amb, I=0.0)

    if Tc_target >= T_amb - 0.5:
        return OFF
    rho_v_air = vapour_density((RH/100.0)*p_sat_buck(T_amb), T_amb)
    # If even the target plate is not cold enough to condense, skip
    if rho_v_air <= vapour_density(p_sat_buck(Tc_target), Tc_target):
        return OFF

    T_h = T_amb + 5.0
    mode='A'; I=0.0; W=0.0; Qc=0.0; mdot=0.0; T_c=Tc_target
    for _ in range(60):
        Th_K = T_h + 273.15
        # ---- try to hold setpoint (Mode A) ----------------------------
        md_t, Qload_t = _cold_loads(T_amb, rho_v_air, Tc_target)
        Tc_K = Tc_target + 273.15
        dT = Th_K - Tc_K
        Aq = 0.5*TEC_R; Bq = -TEC_ALPHA*Tc_K; Cq = Qload_t + TEC_K*dT
        disc = Bq*Bq - 4*Aq*Cq
        I_set = (-Bq - np.sqrt(disc))/(2*Aq) if disc >= 0 else None
        if (I_set is not None) and (0.0 < I_set <= TEC_IMAX):
            mode='A'; I=I_set; T_c=Tc_target; mdot=md_t; Qc=Qload_t
        else:
            # ---- capacity limited: run at Imax, find equilibrium Tc ----
            mode='B'; I=TEC_IMAX
            def f(Tc):
                TcK = Tc + 273.15
                Q_tec = TEC_ALPHA*I*TcK - 0.5*I*I*TEC_R - TEC_K*(Th_K - TcK)
                _, Qld = _cold_loads(T_amb, rho_v_air, Tc)
                return Q_tec - Qld
            lo, hi = Tc_target, T_amb
            flo, fhi = f(lo), f(hi)
            if flo >= 0:
                T_c = Tc_target
            elif fhi <= 0:
                T_c = hi
            else:
                for _b in range(50):
                    mid = 0.5*(lo+hi)
                    if f(mid) > 0: hi = mid
                    else:          lo = mid
                T_c = 0.5*(lo+hi)
            mdot, Qc = _cold_loads(T_amb, rho_v_air, T_c)

        dT = (T_h + 273.15) - (T_c + 273.15)
        W = TEC_ALPHA*I*dT + I*I*TEC_R
        Q_h = Qc + W
        T_h_new = T_amb + Q_h*R_TH_HS
        if abs(T_h_new - T_h) < 0.02:
            T_h = T_h_new; break
        T_h = 0.5*T_h + 0.5*T_h_new

    COP = (Qc/W) if W > 1e-9 else 0.0
    return dict(mode=mode, mdot=mdot, W=W, COP=COP, Qc=Qc,
                Tc=T_c, Th=T_h, I=I)

# ======================================================================
#  LOAD CLIMATE & RUN HOURLY SIMULATION
# ======================================================================

def load_climate():
    df = pd.read_csv(HOURLY_CSV)
    # datetime is YYYYMMDDHH
    df['dt']    = pd.to_datetime(df['datetime'].astype(str), format='%Y%m%d%H')
    df['month'] = df['dt'].dt.month
    df['hour']  = df['dt'].dt.hour
    # NASA POWER fill value -999 guard
    df = df[(df['T2M'] > -100) & (df['RH2M'] >= 0)].copy()
    return df

def run_simulation(df, dt_margin=DT_MARGIN, night_only=True, strategy='smart'):
    """
    Per-hour per-tile simulation. Returns df with hourly results.

    strategy : 'smart'     -> tile runs only when it can hold the setpoint
                              (Mode A); capacity-limited hours are skipped (off).
               'all_night' -> tile runs every night hour (Modes A and B both
                              counted), maximising water at the cost of SEC.
    """
    res = df.copy()
    res['Tdew']  = dew_point_magnus(res['T2M'].values, res['RH2M'].values)
    res['omega'] = humidity_ratio(res['T2M'].values, res['RH2M'].values)

    if night_only:
        window = ((res['hour'] >= NIGHT_START) | (res['hour'] < NIGHT_END))
    else:
        window = pd.Series(True, index=res.index)

    mdot = np.zeros(len(res)); W = np.zeros(len(res))
    cop  = np.zeros(len(res)); Tc = np.full(len(res), np.nan)
    modes = np.array(['off']*len(res), dtype=object)
    for i, (_, row) in enumerate(res.iterrows()):
        if not window.iloc[i]:
            continue
        r = tec_tile_operating_point(row['T2M'], row['RH2M'], dt_margin)
        modes[i] = r['mode']; Tc[i] = r['Tc']
        run_it = (r['mode'] == 'A') if strategy == 'smart' else (r['mode'] != 'off')
        if run_it:
            mdot[i] = r['mdot']; W[i] = r['W']; cop[i] = r['COP']
    res['mode']      = modes
    res['window']    = window.values
    res['operate']   = (mdot > 0) | (W > 0)
    res['mdot_tile'] = mdot                  # kg/s per tile
    res['W_tile']    = W                     # W per tile
    res['COP']       = cop
    res['Tc']        = Tc
    res['water_g_tile'] = mdot*3600.0*1000.0 # g per hour per tile
    res['Wh_tile']      = W*1.0              # Wh per hour per tile (dt=1h)
    return res

# ======================================================================
#  MAIN
# ======================================================================
if __name__ == "__main__":
    print("="*70)
    print(" TEC PV-CLEANING ROBOT — DESIGN & SIMULATION ENGINE")
    print("="*70)

    # ---- Report derived TEC coefficients & cross-check ------------------
    Qc_max_chk = TEC_ALPHA*TEC_IMAX*TEC_THREF - 0.5*TEC_IMAX**2*TEC_R  # at dT=0
    print("\n[TEC1-12706 derived coefficients]")
    print(f"  alpha (Seebeck)      = {TEC_ALPHA:.5f}  V/K")
    print(f"  R (resistance)       = {TEC_R:.4f}  ohm")
    print(f"  K (conductance)      = {TEC_K:.4f}  W/K")
    print(f"  Qc,max(dT=0) check   = {Qc_max_chk:.1f}  W  (datasheet ~51-57 W)")
    print(f"  P_atm at {ELEV_M:.0f} m       = {P_ATM_KPA:.3f}  kPa")
    print(f"  h_conv (cold exch.)  = {H_CONV:.2f}  W/(m^2 K)")
    print(f"  h_mass               = {H_MASS:.5f}  m/s")

    # ---- Spot psychrometrics (design night example) --------------------
    for (T_, RH_) in [(28,25),(20,55),(15,60),(33,18)]:
        print(f"  T={T_:>2} C RH={RH_:>2}% -> Tdew={dew_point_magnus(T_,RH_):5.1f} C, "
              f"omega={humidity_ratio(T_,RH_)*1000:5.2f} g/kg")

    # ---- Load climate & run baseline simulation -------------------------
    df = load_climate()
    print(f"\n[Climate] {len(df)} valid hourly records "
          f"({df['dt'].min()} -> {df['dt'].max()})")

    # Strategy comparison: 'smart' (efficient, setpoint-only) is the design
    # basis; 'all_night' is reported for contrast.
    sim_all = run_simulation(df, dt_margin=DT_MARGIN, night_only=True,
                             strategy='all_night')
    sim     = run_simulation(df, dt_margin=DT_MARGIN, night_only=True,
                             strategy='smart')

    night = sim[sim['window']]
    mode_frac = night['mode'].value_counts(normalize=True)*100
    print("\n[Night-hour mode distribution] (margin=5 K)")
    for m in ['A','B','off']:
        print(f"  mode {m:>3}: {mode_frac.get(m,0.0):5.1f} %")

    def per_tile_stats(s):
        o = s[s['operate']]
        w = o['mdot_tile'].sum()*3600.0          # kg/yr
        e = o['Wh_tile'].sum()/1000.0            # kWh/yr
        c = o[o['COP']>0]['COP'].mean()
        return w, e, c, len(o)
    w_all,e_all,c_all,_ = per_tile_stats(sim_all)
    w_sm ,e_sm ,c_sm ,h_sm = per_tile_stats(sim)
    print("\n[Per-tile annual yield — strategy comparison]")
    print(f"  all_night : {w_all:6.2f} L/yr, {e_all:6.2f} kWh/yr, "
          f"SEC {e_all/w_all if w_all else 0:5.2f} kWh/L, COP {c_all:.3f}")
    print(f"  smart     : {w_sm:6.2f} L/yr, {e_sm:6.2f} kWh/yr, "
          f"SEC {e_sm/w_sm if w_sm else 0:5.2f} kWh/L, COP {c_sm:.3f}, "
          f"{h_sm} op-hours/yr")

    # Design basis = smart strategy
    op = sim[sim['operate']]
    water_per_tile_year  = w_sm                                  # kg/yr per tile
    energy_per_tile_year = e_sm*1000.0                           # Wh/yr per tile
    water_per_tile_day   = water_per_tile_year/365.0*1000.0      # g/day per tile
    cop_op = op[op['COP']>0]['COP']
    print("\n[Per-tile DESIGN basis: smart night operation, margin=5 K]")
    print(f"  Annual water / tile   = {water_per_tile_year:.2f} L")
    print(f"  Daily water / tile    = {water_per_tile_day:.1f} g/day")
    print(f"  Annual energy / tile  = {energy_per_tile_year/1000.0:.2f} kWh")
    print(f"  Mean COP (operating)  = {cop_op.mean():.3f}")
    print(f"  Useful op-hours/day   = {h_sm/365.0:.1f} h")

    # ---- Number of tiles for target -------------------------------------
    if water_per_tile_day > 0:
        N_lo = TARGET_LDAY_LO*1000.0 / water_per_tile_day
        N_hi = TARGET_LDAY_HI*1000.0 / water_per_tile_day
    else:
        N_lo = N_hi = np.nan
    N_tiles = int(np.ceil(N_hi))   # size for the high target (1.0 L/day)
    print(f"\n[Tile sizing]  for {TARGET_LDAY_LO} L/day -> {N_lo:.1f} tiles ; "
          f"for {TARGET_LDAY_HI} L/day -> {N_hi:.1f} tiles")
    print(f"  -> select N_tiles = {N_tiles} (sized to {TARGET_LDAY_HI} L/day)")

    # ---- System-level water, energy, SEC --------------------------------
    water_day_L   = water_per_tile_day*N_tiles/1000.0           # L/day system
    sec_kWh_per_L = (energy_per_tile_year/1000.0) / water_per_tile_year \
                    if water_per_tile_year>0 else np.nan        # kWh/kg=kWh/L
    print(f"\n[System AWH]  N={N_tiles} tiles")
    print(f"  Water         = {water_day_L:.2f} L/day  ({water_day_L*365:.0f} L/yr)")
    print(f"  SEC           = {sec_kWh_per_L:.2f} kWh/L (thermo+sensible, excl. parasitics)")

    # ---- Full robot daily energy budget ---------------------------------
    op_hours_per_day = (NIGHT_START==18 and NIGHT_END==6) and 12 or 12
    # TEC electrical energy per day (system) = per-tile night Wh * N / 365
    E_tec_day_Wh   = energy_per_tile_year*N_tiles/365.0
    n_fans         = 2*int(np.ceil(N_tiles/4.0))
    E_fans_day_Wh  = n_fans*P_FAN_EACH*op_hours_per_day
    E_mcu_day_Wh   = P_MCU*24.0
    # cleaning event timing (boustrophedon)
    w_eff   = BRUSH_W*(1-OVERLAP)
    n_pass  = int(np.ceil(PANEL_AREA/ (2.0*w_eff)))  # panel ~1 m wide x 2 m
    # treat panel as 1.0 m (width) x 2.0 m (length); passes across width
    width_m = 1.0; length_m = 2.0
    n_pass  = int(np.ceil(width_m/w_eff))
    path_len = n_pass*length_m + (n_pass-1)*w_eff
    t_clean_s = path_len/V_CLEAN + (n_pass-1)*3.0    # +3 s per turn
    # cleaning frequency: enough events to use harvested water
    events_per_year = water_day_L*365.0 / WATER_PER_EVENT
    E_clean_event_Wh = (P_PUMP+P_DRIVE)*(t_clean_s/3600.0)
    E_clean_day_Wh   = E_clean_event_Wh*events_per_year/365.0
    E_day_total_Wh   = E_tec_day_Wh + E_fans_day_Wh + E_mcu_day_Wh + E_clean_day_Wh
    print("\n[Daily energy budget — system]")
    print(f"  TEC stack ({N_tiles} tiles)  = {E_tec_day_Wh:7.1f} Wh/day")
    print(f"  Fans ({n_fans})             = {E_fans_day_Wh:7.1f} Wh/day")
    print(f"  MCU + sensors          = {E_mcu_day_Wh:7.1f} Wh/day")
    print(f"  Cleaning (motors+pump) = {E_clean_day_Wh:7.1f} Wh/day "
          f"({events_per_year:.1f} events/yr, t_clean={t_clean_s:.0f} s)")
    print(f"  TOTAL                  = {E_day_total_Wh:7.1f} Wh/day "
          f"= {E_day_total_Wh/1000.0:.3f} kWh/day")
    sec_full = (E_day_total_Wh/1000.0)/water_day_L if water_day_L>0 else np.nan
    print(f"  Full-system SEC        = {sec_full:.2f} kWh/L (incl. parasitics)")

    # ---- Dedicated PV & battery sizing ----------------------------------
    P_pv_Wp   = (E_day_total_Wh/1000.0)/(PSH_BENBAN*PR_PV)*1000.0  # Wp
    A_pv_m2   = P_pv_Wp/1000.0/ETA_PV_MOD
    # battery: store one night of operation (autonomy) + cleaning
    E_store_Wh = E_tec_day_Wh + E_fans_day_Wh + 0.5*E_mcu_day_Wh
    C_batt_Ah  = BATT_MARGIN*E_store_Wh/(V_BATT*DOD*ETA_CHG)
    print("\n[Power supply sizing]")
    print(f"  Dedicated PV          = {P_pv_Wp:.0f} Wp  (~{A_pv_m2:.2f} m^2 module area)")
    print(f"  Battery capacity      = {C_batt_Ah:.1f} Ah @ {V_BATT:.0f} V "
          f"({C_batt_Ah*V_BATT:.0f} Wh, {DOD*100:.0f}% DOD)")

    # ---- Robot traction torque check ------------------------------------
    alpha_r = np.radians(PANEL_TILT)
    F_resist = (M_ROBOT*G*np.sin(alpha_r) + MU_ROLL*M_ROBOT*G*np.cos(alpha_r))
    T_traction = F_resist*R_WHEEL/ETA_DRIVE     # total at wheels [N m]
    F_noslip   = MU_ROLL*M_ROBOT*G*np.cos(alpha_r)
    print("\n[Drive mechanics]")
    print(f"  Resistive force       = {F_resist:.1f} N (on {PANEL_TILT:.0f} deg tilt)")
    print(f"  Traction torque (tot) = {T_traction:.3f} N m -> {T_traction/2:.3f} N m per motor")
    print(f"  Cleaning passes       = {n_pass}, path = {path_len:.1f} m, "
          f"t_clean = {t_clean_s:.0f} s")

    # ---- Heat-sink requirement ------------------------------------------
    Qh_tile_peak = op['Qc'].max() if 'Qc' in op else np.nan
    # recompute peak Qh
    peak = op.loc[op['W_tile'].idxmax()] if len(op)>0 else None
    print("\n[Hot-side heat sink]")
    print(f"  R_th,hs assumed       = {R_TH_HS:.2f} K/W per tile")

    # ==================================================================
    #  MONTHLY AGGREGATES (for figures & LaTeX tables)
    # ==================================================================
    monthly = sim.groupby('month').agg(
        T2M=('T2M','mean'), RH2M=('RH2M','mean'),
        Tdew=('Tdew','mean'), omega=('omega','mean')).reset_index()
    # monthly system water (L) and energy (kWh)
    mw = op.groupby('month').agg(
        mdot=('mdot_tile','sum'), Wh=('Wh_tile','sum'),
        COP=('COP', lambda s: s[s>0].mean())).reset_index()
    mw['water_L_sys'] = mw['mdot']*3600.0*N_tiles            # L per month (per tile-> *N)
    mw['energy_kWh_sys'] = mw['Wh']*N_tiles/1000.0
    monthly = monthly.merge(mw[['month','water_L_sys','energy_kWh_sys','COP']],
                            on='month', how='left')
    monthly['water_Lday_sys'] = monthly['water_L_sys'] / \
        monthly['month'].map(lambda m: pd.Timestamp(2020,m,1).days_in_month)
    monthly['days_to_charge'] = WATER_PER_EVENT/monthly['water_Lday_sys']
    monthly.to_csv(os.path.join(OUT_DIR,'tec_robot_monthly.csv'), index=False,
                   float_format='%.4f')
    print("\n[Monthly summary written] output/tec_robot_monthly.csv")
    print(monthly[['month','T2M','RH2M','Tdew','water_Lday_sys',
                   'COP','days_to_charge']].round(2).to_string(index=False))

    # ==================================================================
    #  COOLING-MARGIN SENSITIVITY  (yield & SEC vs sub-cooling)
    # ==================================================================
    margins = [2,3,5,8,10]
    sens = []
    for mgn in margins:
        s2 = run_simulation(df, dt_margin=mgn, night_only=True)
        o2 = s2[s2['operate']]
        w_tile_yr = o2['mdot_tile'].sum()*3600.0
        e_tile_yr = o2['Wh_tile'].sum()/1000.0
        sec = e_tile_yr/w_tile_yr if w_tile_yr>0 else np.nan
        sens.append(dict(margin=mgn, water_tile_Lyr=w_tile_yr,
                         sec_kWh_L=sec,
                         cop=o2[o2['COP']>0]['COP'].mean()))
    sens = pd.DataFrame(sens)
    sens.to_csv(os.path.join(OUT_DIR,'tec_margin_sensitivity.csv'),
                index=False, float_format='%.4f')
    print("\n[Margin sensitivity]")
    print(sens.round(3).to_string(index=False))

    # ==================================================================
    #  THEORETICAL COP / SEC vs dT  (single-tile characteristic)
    # ==================================================================
    dT_range = np.arange(5,55,1.0)
    cop_curve=[]; sec_curve=[]
    for dT in dT_range:
        # representative: Tc=10 degC, Th=Tc+dT, run at COP-optimal current
        Tc_K=283.15; Th_K=Tc_K+dT
        # sweep I, find max COP with positive Qc
        Is=np.linspace(0.1,TEC_IMAX,200)
        Qc=TEC_ALPHA*Is*Tc_K-0.5*Is**2*TEC_R-TEC_K*dT
        W =TEC_ALPHA*Is*dT+Is**2*TEC_R
        with np.errstate(divide='ignore',invalid='ignore'):
            COPs=np.where(Qc>0,Qc/W,0.0)
        cop_curve.append(np.nanmax(COPs))
        sec_curve.append( (h_fg(10.0)/3.6e6)/np.nanmax(COPs) if np.nanmax(COPs)>0 else np.nan)
    cop_curve=np.array(cop_curve); sec_curve=np.array(sec_curve)

    # ==================================================================
    #  WRITE VERIFIED-NUMBERS JSON  (single source for the .tex)
    # ==================================================================
    results = dict(
        tec=dict(alpha=TEC_ALPHA, R=TEC_R, K=TEC_K, Qc_max_check=Qc_max_chk,
                 price_egp=TEC_PRICE_EGP, price_usd=TEC_PRICE_EGP/EGP_PER_USD),
        site=dict(P_atm_kPa=P_ATM_KPA, h_conv=H_CONV, h_mass=H_MASS),
        per_tile=dict(water_Lyr=water_per_tile_year,
                      water_gday=water_per_tile_day,
                      energy_kWhyr=energy_per_tile_year/1000.0,
                      mean_COP=float(cop_op.mean())),
        sizing=dict(N_lo=float(N_lo), N_hi=float(N_hi), N_tiles=N_tiles,
                    water_Lday=water_day_L, sec_thermo=sec_kWh_per_L,
                    sec_full=sec_full),
        energy=dict(E_tec_Wh=E_tec_day_Wh, E_fans_Wh=E_fans_day_Wh,
                    E_mcu_Wh=E_mcu_day_Wh, E_clean_Wh=E_clean_day_Wh,
                    E_total_Wh=E_day_total_Wh, n_fans=n_fans),
        supply=dict(P_pv_Wp=P_pv_Wp, A_pv_m2=A_pv_m2, C_batt_Ah=C_batt_Ah,
                    E_store_Wh=E_store_Wh),
        mechanics=dict(F_resist=F_resist, T_traction=T_traction,
                       n_pass=n_pass, path_len=path_len, t_clean_s=t_clean_s),
        cleaning=dict(water_per_event=WATER_PER_EVENT,
                      events_per_year=events_per_year),
    )
    with open(os.path.join(OUT_DIR,'tec_robot_results.json'),'w') as f:
        json.dump(results, f, indent=2)
    print("\n[Verified numbers written] output/tec_robot_results.json")

    # ==================================================================
    #  FIGURES  (IEEE single-column, serif, 300 dpi PDF)
    # ==================================================================
    mpl.rcParams.update({
        'font.family':'serif','font.size':10,'axes.labelsize':10,
        'legend.fontsize':8,'xtick.labelsize':9,'ytick.labelsize':9,
        'axes.grid':True,'grid.alpha':0.3,'lines.linewidth':1.5,
        'figure.figsize':(3.5,2.8),'savefig.dpi':300,'savefig.bbox':'tight'})
    MON=['J','F','M','A','M','J','J','A','S','O','N','D']

    # Fig 1: monthly climate (T, RH, dew point)
    fig,ax=plt.subplots()
    ax.plot(monthly['month'],monthly['T2M'],'-o',ms=3,color='#d62728',label=r'$T_{amb}$')
    ax.plot(monthly['month'],monthly['Tdew'],'-s',ms=3,color='#1f77b4',label=r'$T_{dew}$')
    ax.set_xlabel('Month'); ax.set_ylabel(r'Temperature ($^\circ$C)')
    ax2=ax.twinx(); ax2.plot(monthly['month'],monthly['RH2M'],'--^',ms=3,
                             color='#2ca02c',label='RH'); ax2.set_ylabel('RH (%)')
    ax2.grid(False)
    ax.set_xticks(range(1,13)); ax.set_xticklabels(MON)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper right',ncol=1)
    fig.savefig(os.path.join(FIG_DIR,'fig_monthly_climate.pdf')); plt.close(fig)

    # Fig 2: monthly system water yield & days-to-charge
    fig,ax=plt.subplots()
    ax.bar(monthly['month'],monthly['water_Lday_sys'],color='#1f77b4',
           alpha=0.8,label='Water yield')
    ax.set_xlabel('Month'); ax.set_ylabel('Water (L/day)')
    ax.axhline(TARGET_LDAY_LO,ls=':',color='grey'); ax.axhline(TARGET_LDAY_HI,ls=':',color='grey')
    ax2=ax.twinx(); ax2.plot(monthly['month'],monthly['days_to_charge'],'-o',
                             ms=3,color='#ff7f0e',label='Days to 3.6 L');
    ax2.set_ylabel('Days to fill cleaning charge'); ax2.grid(False)
    ax.set_xticks(range(1,13)); ax.set_xticklabels(MON)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper center')
    fig.savefig(os.path.join(FIG_DIR,'fig_monthly_water.pdf')); plt.close(fig)

    # Fig 3: COP & SEC vs dT
    fig,ax=plt.subplots()
    ax.plot(dT_range,cop_curve,'-',color='#1f77b4',label='COP')
    ax.set_xlabel(r'$\Delta T = T_H-T_C$ (K)'); ax.set_ylabel('COP (max)')
    ax2=ax.twinx(); ax2.plot(dT_range,sec_curve,'--',color='#d62728',label='SEC')
    ax2.set_ylabel('SEC (kWh/L, latent only)'); ax2.grid(False)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper right')
    fig.savefig(os.path.join(FIG_DIR,'fig_cop_sec_dT.pdf')); plt.close(fig)

    # Fig 4: margin sensitivity
    fig,ax=plt.subplots()
    ax.plot(sens['margin'],sens['water_tile_Lyr'],'-o',ms=4,color='#1f77b4',
            label='Water/tile')
    ax.set_xlabel(r'Sub-cooling margin $\Delta T_{margin}$ (K)')
    ax.set_ylabel('Annual water/tile (L)')
    ax2=ax.twinx(); ax2.plot(sens['margin'],sens['sec_kWh_L'],'--s',ms=4,
                             color='#d62728',label='SEC')
    ax2.set_ylabel('SEC (kWh/L)'); ax2.grid(False)
    l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
    ax.legend(l1+l2,la1+la2,loc='upper left')
    fig.savefig(os.path.join(FIG_DIR,'fig_margin_sensitivity.pdf')); plt.close(fig)

    # Fig 5: energy balance - monthly TEC+aux energy vs dedicated PV supply
    fig,ax=plt.subplots()
    days=monthly['month'].map(lambda m: pd.Timestamp(2020,m,1).days_in_month)
    e_demand = monthly['energy_kWh_sys'] + (E_fans_day_Wh+E_mcu_day_Wh)*days/1000.0
    e_supply = P_pv_Wp/1000.0*PSH_BENBAN*PR_PV*days
    ax.bar(monthly['month']-0.18,e_demand,width=0.36,color='#d62728',
           alpha=0.8,label='Demand')
    ax.bar(monthly['month']+0.18,e_supply,width=0.36,color='#2ca02c',
           alpha=0.8,label='PV supply')
    ax.set_xlabel('Month'); ax.set_ylabel('Energy (kWh/month)')
    ax.set_xticks(range(1,13)); ax.set_xticklabels(MON); ax.legend()
    fig.savefig(os.path.join(FIG_DIR,'fig_energy_balance.pdf')); plt.close(fig)

    # Fig 6: diurnal profiles summer (Jul) vs winter (Jan)
    fig,ax=plt.subplots()
    for mth,c,lab in [(1,'#1f77b4','Jan'),(7,'#d62728','Jul')]:
        d=sim[sim['month']==mth].groupby('hour').agg(
            T=('T2M','mean'),Td=('Tdew','mean')).reset_index()
        ax.plot(d['hour'],d['T'],'-',color=c,label=f'{lab} $T_{{amb}}$')
        ax.plot(d['hour'],d['Td'],'--',color=c,label=f'{lab} $T_{{dew}}$')
    ax.axvspan(0,NIGHT_END,color='grey',alpha=0.12)
    ax.axvspan(NIGHT_START,23,color='grey',alpha=0.12)
    ax.set_xlabel('Hour of day'); ax.set_ylabel(r'Temperature ($^\circ$C)')
    ax.set_xlim(0,23); ax.legend(ncol=2,fontsize=7)
    fig.savefig(os.path.join(FIG_DIR,'fig_diurnal.pdf')); plt.close(fig)

    print("\n[Figures written] 6 PDFs in figures/")
    print("="*70)
    print(" DONE")
    print("="*70)
