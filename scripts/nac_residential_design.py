"""
===================================================================
Script:      nac_residential_design.py
Author:      Graduation Project — Autonomous TEC PV-Cleaning Robot
Date:        2026-06-12
Purpose:     Re-site the reference design to a RESIDENTIAL ROOFTOP in
             the New Administrative Capital (NAC, 30.03 N 31.73 E).

             Stage 1: fetch NASA POWER hourly T2M/RH2M/PRECTOTCORR/
                      ALLSKY_SFC_SW_DWN for NAC, calendar year 2025,
                      -> output/nac_nasa_power_hourly.csv
             Stage 2: rerun the frozen TEC tile model of
                      scripts/tec_robot_design.py on the NAC climate
                      (module imported, site constants patched; the
                      physics and TEC coefficients are untouched).
             Stage 3: residential array sizing — 18 x 550 Wp LONGi
                      LR5-72HPH-550M (2.556 m2 each, 46.0 m2 total),
                      tilt 26 deg, cleaning 1.8 L/m2 per event.
                      Dockside AWG sized to a FRACTION of annual
                      cleaning demand (honest sizing), PV + battery
                      for the dock, tank, robot mechanics at 26 deg.
             Outputs: output/nac_tec_robot_monthly.csv
                      output/nac_tec_robot_results.json
                      figures/nac_monthly_water.pdf
             Benban files are NOT overwritten.
===================================================================
"""

import os, sys, csv, json
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
OUT  = os.path.join(ROOT, "output")
FIG  = os.path.join(ROOT, "figures")
os.makedirs(OUT, exist_ok=True); os.makedirs(FIG, exist_ok=True)

NAC_LAT, NAC_LON = 30.03, 31.73
YEAR = 2025
NAC_CSV = os.path.join(OUT, "nac_nasa_power_hourly.csv")

# ----------------------------------------------------------------------
# Stage 1 — fetch NASA POWER hourly for NAC (skip if already on disk)
# ----------------------------------------------------------------------
def fetch_nac():
    if os.path.exists(NAC_CSV):
        print("[fetch] cached:", NAC_CSV);
        with open(os.path.join(OUT, "nac_site_meta.json")) as f:
            return json.load(f)["elevation_m"]
    base = "https://power.larc.nasa.gov/api/temporal/hourly/point"
    q = dict(parameters="T2M,RH2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
             community="RE", longitude=NAC_LON, latitude=NAC_LAT,
             start=f"{YEAR}0101", end=f"{YEAR}1231", format="JSON")
    url = f"{base}?{urlencode(q)}"
    print("[fetch] GET", url[:110], "...")
    with urlopen(url, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("messages"):
        print("[fetch] API messages:", data["messages"])
    elev = data.get("geometry", {}).get("coordinates", [None, None, None])[2]
    par = data["properties"]["parameter"]
    keys = list(par.keys())
    times = sorted(par[keys[0]].keys())
    with open(NAC_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["datetime"] + keys)
        w.writeheader()
        for t in times:
            row = {"datetime": t}
            for k in keys:
                row[k] = par[k].get(t)
            w.writerow(row)
    with open(os.path.join(OUT, "nac_site_meta.json"), "w") as f:
        json.dump(dict(lat=NAC_LAT, lon=NAC_LON, year=YEAR,
                       elevation_m=elev, source="NASA POWER hourly API"), f, indent=2)
    print(f"[fetch] wrote {NAC_CSV}  rows={len(times)}  elev={elev} m")
    return elev

elev_m = fetch_nac()
if elev_m is None:
    elev_m = 350.0   # plateau east of Cairo; pressure effect is < 2 %

# ----------------------------------------------------------------------
# Stage 2 — rerun the frozen tile model on NAC climate
# ----------------------------------------------------------------------
sys.path.insert(0, HERE)
import tec_robot_design as base

base.HOURLY_CSV = NAC_CSV
base.P_ATM_KPA  = 101.325 * (1.0 - 2.25577e-5 * float(elev_m)) ** 5.2559

df = base.load_climate()
print(f"[climate] {len(df)} valid hourly records "
      f"({df['dt'].min()} -> {df['dt'].max()})")

sim = base.run_simulation(df, dt_margin=base.DT_MARGIN,
                          night_only=True, strategy='smart')
op = sim[sim['operate']]

w_tile_yr = op['mdot_tile'].sum() * 3600.0          # L/yr per tile
e_tile_yr = op['Wh_tile'].sum() / 1000.0            # kWh/yr per tile
cop_mean  = op[op['COP'] > 0]['COP'].mean()
op_h_yr   = len(op)
w_tile_gd = w_tile_yr / 365.0 * 1000.0              # g/day
sec_thermo = e_tile_yr / w_tile_yr

print(f"[per-tile NAC] water={w_tile_yr:.2f} L/yr ({w_tile_gd:.1f} g/day), "
      f"energy={e_tile_yr:.2f} kWh/yr, SEC={sec_thermo:.2f} kWh/L, "
      f"COP={cop_mean:.3f}, op-hours={op_h_yr}")

# ---- PSH at NAC from fetched irradiance --------------------------------
days_in_year = df['dt'].dt.date.nunique()
ghi_kwh_m2_d = df['ALLSKY_SFC_SW_DWN'].clip(lower=0).sum() / 1000.0 / days_in_year
print(f"[site] GHI = {ghi_kwh_m2_d:.2f} kWh/m2/day (PSH), elev = {elev_m:.0f} m")

# ---- Monthly aggregates -------------------------------------------------
mon_clim = sim.groupby('month').agg(T2M=('T2M','mean'), RH2M=('RH2M','mean'),
                                    Tdew=('Tdew','mean')).reset_index()
mon_op = op.groupby('month').agg(mdot=('mdot_tile','sum'),
                                 Wh=('Wh_tile','sum'),
                                 COP=('COP', lambda s: s[s>0].mean())).reset_index()
mon = mon_clim.merge(mon_op, on='month', how='left').fillna(0.0)
dim = mon['month'].map(lambda m: pd.Timestamp(YEAR, m, 1).days_in_month)
mon['water_L_tile']    = mon['mdot'] * 3600.0                 # L/month per tile
mon['water_gday_tile'] = mon['water_L_tile'] / dim * 1000.0
mon['energy_kWh_tile'] = mon['Wh'] / 1000.0

# ----------------------------------------------------------------------
# Stage 3 — residential array, cleaning demand, dock AWG sizing
# ----------------------------------------------------------------------
N_MOD   = 18
P_MOD   = 550.0                  # Wp, LONGi LR5-72HPH-550M
A_MOD   = 2.256 * 1.133          # m2 = 2.556
A_ARR   = N_MOD * A_MOD          # 46.0 m2
P_ARR   = N_MOD * P_MOD / 1000.0 # 9.9 kWp
TILT    = 26.0                   # deg
# Cleaning water intensity. The robot is a microfibre brush + light spray, not
# a hose, so the design uses 0.3 L/m2 per pass (damp-microfibre robotic
# cleaning, within the 0.1-0.5 L/m2 band reported for water-assisted PV
# cleaners) rather than the 1.8 L/m2 wet-wash figure of the first baseline.
# This 6x cut is what makes full water self-supply feasible.
W_M2    = 0.3                    # L/m2 per event (was 1.8 wet-wash)
W_EVENT = W_M2 * A_ARR           # L per whole-array event
F_DAYS  = 3.5                    # cleaning interval, days (3-4 day band)
F_WEEK  = 7.0
ev_yr   = 365.0 / F_DAYS
ev_yr_w = 365.0 / F_WEEK
D_YR    = W_EVENT * ev_yr        # annual demand, baseline
D_YR_W  = W_EVENT * ev_yr_w      # annual demand, weekly option

# ---- self-supply fraction trade study ----------------------------------
def dock(f_supply, demand_yr):
    """Size the dock AWG for a self-supply fraction of annual demand."""
    target_Lyr = f_supply * demand_yr
    N = int(np.ceil(target_Lyr / w_tile_yr))
    n_fans = 2 * int(np.ceil(N / 4.0))
    E_tec  = e_tile_yr * 1000.0 * N / 365.0                   # Wh/day
    E_fans = n_fans * base.P_FAN_EACH * 12.0
    E_mcu  = base.P_MCU * 24.0
    E_tot  = E_tec + E_fans + E_mcu                           # Wh/day (dock)
    P_pv   = E_tot / 1000.0 / (ghi_kwh_m2_d * base.PR_PV) * 1000.0   # Wp
    E_sto  = E_tec + E_fans + 0.5 * E_mcu
    C_batt = base.BATT_MARGIN * E_sto / (base.V_BATT * base.DOD * base.ETA_CHG)
    # ---- cost (MARKET_BOM.tex unit prices, EGP, June 2026) ----
    c_tiles = N * 120
    c_ext   = N * 0.13 * 700
    c_fans  = n_fans * 180
    c_plate = N * 26                 # 1800 EGP / 69 tiles
    c_sw    = int(np.ceil(N / 4.0)) * 40 + 750   # MOSFETs + misc
    c_awg   = c_tiles + c_ext + c_fans + c_plate + c_sw
    n_pv    = int(np.ceil(P_pv / 580.0))
    c_pv    = n_pv * 7500
    I_chg   = n_pv * 580.0 / 12.0
    n_mppt  = int(np.ceil(I_chg / 60.0))
    c_mppt  = n_mppt * 9500
    n_pack  = int(np.ceil(C_batt / 200.0))
    c_batt  = n_pack * 32000
    c_dock  = c_awg + c_pv + c_mppt + c_batt
    return dict(f=f_supply, target_Lyr=target_Lyr, N_tiles=N, n_fans=n_fans,
                E_day_Wh=E_tot, P_pv_Wp=P_pv, n_pv_mod=n_pv,
                C_batt_Ah=C_batt, n_pack=n_pack,
                cost=dict(awg=c_awg, pv=c_pv, mppt=c_mppt, batt=c_batt,
                          dock_total=c_dock))

trade = [dock(f, D_YR) for f in (0.25, 0.50, 1.00)]
trade_weekly = [dock(f, D_YR_W) for f in (0.25, 0.50, 1.00)]

print("\n[self-supply trade, 3.5-day cleaning]")
for t in trade:
    print(f"  f={t['f']:.2f}: N={t['N_tiles']:4d} tiles, "
          f"E={t['E_day_Wh']/1000:.2f} kWh/d, PV={t['P_pv_Wp']:.0f} Wp, "
          f"batt={t['C_batt_Ah']:.0f} Ah, dock={t['cost']['dock_total']:,} EGP")
print("[self-supply trade, weekly cleaning]")
for t in trade_weekly:
    print(f"  f={t['f']:.2f}: N={t['N_tiles']:4d} tiles, "
          f"E={t['E_day_Wh']/1000:.2f} kWh/d, PV={t['P_pv_Wp']:.0f} Wp, "
          f"batt={t['C_batt_Ah']:.0f} Ah, dock={t['cost']['dock_total']:,} EGP")

# ---- robot mechanics at 26 deg ------------------------------------------
alpha = np.radians(TILT)
F_res = base.M_ROBOT * base.G * (np.sin(alpha) + base.MU_ROLL * np.cos(alpha))
T_trac = F_res * base.R_WHEEL / base.ETA_DRIVE
w_eff = base.BRUSH_W * (1 - base.OVERLAP)
n_pass = int(np.ceil(1.133 / w_eff))
path_mod = n_pass * 2.256 + (n_pass - 1) * w_eff
t_mod = path_mod / base.V_CLEAN + (n_pass - 1) * 3.0
path_evt = path_mod * N_MOD
E_clean_evt = (base.P_PUMP + base.P_DRIVE) * (t_mod * N_MOD / 3600.0)
print(f"\n[mechanics @26deg] F={F_res:.1f} N, T={T_trac:.3f} N m total "
      f"({T_trac/2:.3f} per motor); per-module path {path_mod:.1f} m, "
      f"{t_mod:.0f} s; event path {path_evt:.0f} m, "
      f"E_clean={E_clean_evt:.0f} Wh/event")

# ---- write outputs ------------------------------------------------------
mon_out = mon[['month','T2M','RH2M','Tdew','water_L_tile','water_gday_tile',
               'energy_kWh_tile','COP']]
mon_out.to_csv(os.path.join(OUT, "nac_tec_robot_monthly.csv"),
               index=False, float_format='%.4f')

results = dict(
    site=dict(name="New Administrative Capital", lat=NAC_LAT, lon=NAC_LON,
              year=YEAR, elevation_m=float(elev_m),
              P_atm_kPa=base.P_ATM_KPA, PSH=ghi_kwh_m2_d),
    per_tile=dict(water_Lyr=w_tile_yr, water_gday=w_tile_gd,
                  energy_kWhyr=e_tile_yr, sec_kWh_L=sec_thermo,
                  mean_COP=float(cop_mean), op_hours_yr=int(op_h_yr)),
    array=dict(n_modules=N_MOD, p_mod_Wp=P_MOD, a_mod_m2=A_MOD,
               area_m2=A_ARR, p_kWp=P_ARR, tilt_deg=TILT),
    cleaning=dict(L_per_m2=W_M2, L_per_event=W_EVENT,
                  interval_days=F_DAYS, events_yr=ev_yr,
                  demand_Lyr=D_YR, demand_Lyr_weekly=D_YR_W),
    trade_3p5day=trade, trade_weekly=trade_weekly,
    mechanics=dict(tilt_deg=TILT, F_resist=F_res, T_traction=T_trac,
                   n_pass=n_pass, path_module_m=path_mod, t_module_s=t_mod,
                   path_event_m=path_evt, E_clean_event_Wh=E_clean_evt),
)
with open(os.path.join(OUT, "nac_tec_robot_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("[written] output/nac_tec_robot_monthly.csv, nac_tec_robot_results.json")

# ---- figure: monthly per-tile water, NAC vs Benban ----------------------
mpl.rcParams.update({
    'font.family':'serif','font.size':10,'axes.labelsize':10,
    'legend.fontsize':8,'xtick.labelsize':9,'ytick.labelsize':9,
    'axes.grid':True,'grid.alpha':0.3,'lines.linewidth':1.5,
    'figure.figsize':(5.2,3.2),'savefig.dpi':300,'savefig.bbox':'tight'})
MON = ['J','F','M','A','M','J','J','A','S','O','N','D']

ben = pd.read_csv(os.path.join(OUT, "tec_robot_monthly.csv"))
# Benban monthly CSV stores system water for 69 tiles -> per tile
ben_tile_gday = ben['water_Lday_sys'] / 69.0 * 1000.0

fig, ax = plt.subplots()
ax.bar(mon['month']-0.19, mon['water_gday_tile'], width=0.38,
       color='#1f77b4', alpha=0.85, label=f'NAC {YEAR}')
ax.bar(ben['month']+0.19, ben_tile_gday, width=0.38,
       color='#d62728', alpha=0.85, label='Benban 2020')
ax.set_xlabel('Month'); ax.set_ylabel('Condensate per tile (g/day)')
ax.set_xticks(range(1,13)); ax.set_xticklabels(MON)
ax.legend(loc='upper center', ncol=2)
fig.savefig(os.path.join(FIG, "nac_monthly_water.pdf")); plt.close(fig)
print("[figure] figures/nac_monthly_water.pdf")
