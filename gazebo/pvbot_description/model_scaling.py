#!/usr/bin/env python3
"""
model_scaling.py -- extends model_calcs.py with:
  (A) a tilt + rolling-friction sensitivity sweep of the climb margin, with the
      critical tilt at which the 45 N drive ceiling is exhausted, and
  (B) three-scale deployment scaling (commercial rooftop / residential rooftop /
      street-lamp PV), anchored on the validated NAC residential model point.

Outputs:
  fig_tilt_margin.pdf / .png   -- climb-margin vs tilt curves
  model_scaling_results.json   -- variant table + critical tilts
Run:  python model_scaling.py
"""
import json
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
g = 9.81

# ---- model anchors (same as model_calcs.py / the NAC results) ----
m = 8.0                 # kg carriage
F_b = 1.73              # N brush drag
F_ceiling = 45.0        # N drive ceiling
design_tilt = 24.0      # deg
L_per_m2 = 0.3          # L/m^2 per clean
tank_L = 3.6            # L carriage tank
clean_interval_d = 3.5  # days between cleans
rate_m2h = 108.0        # m^2/h cleaning-only (from model_calcs)
duty_field = 0.60
solar_h = 8.0
unit_capacity_m2day = rate_m2h * duty_field * solar_h   # ~518 m^2/day per unit

# NAC residential anchor (output/nac_tec_robot_results.json)
area_per_kWp = 46.008864 / 9.9      # = 4.647 m^2/kWp (18x550 Wp, 46 m^2)
tile_water_Lday = 0.10597           # L/day per TEC1-12706 tile at NAC
tile_energy_kWhyr = 56.03           # kWh/yr per tile
PSH = 5.71                          # peak sun hours/day at NAC
pv_derate = 0.75
# PV per tile from its daily energy:  Wh/day / PSH / derate
pv_Wp_per_tile = (tile_energy_kWhyr * 1000 / 365) / PSH / pv_derate

# --------------------------------------------------------------------------
# (A) TILT + FRICTION SENSITIVITY
# --------------------------------------------------------------------------
def margin(theta_deg, mu):
    th = math.radians(theta_deg)
    F = m * g * (math.sin(th) + mu * math.cos(th)) + F_b
    return F_ceiling / F

def critical_tilt(mu):
    """tilt where margin == 1 (drive ceiling exhausted)."""
    lo, hi = 0.0, 60.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if margin(mid, mu) > 1.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)

mus = [0.03, 0.05, 0.08]
thetas = np.linspace(0, 35, 400)
crit = {mu: critical_tilt(mu) for mu in mus}

fig, ax = plt.subplots(figsize=(6.4, 3.8))
colors = {0.03: "#2E7D32", 0.05: "#1F4E79", 0.08: "#C0392B"}
for mu in mus:
    ax.plot(thetas, [margin(t, mu) for t in thetas],
            color=colors[mu], lw=2, label=fr"$\mu_r={mu:.2f}$  (crit {crit[mu]:.1f}$^\circ$)")
ax.axhline(1.0, color="k", ls="--", lw=1)
ax.text(0.4, 1.03, "margin = 1 (drive ceiling)", fontsize=8)
ax.axvline(design_tilt, color="grey", ls=":", lw=1.2)
ax.text(design_tilt + 0.3, ax.get_ylim()[1] * 0.92, "design 24$^\\circ$",
        fontsize=8, color="grey")
m24 = margin(design_tilt, 0.05)
ax.plot([design_tilt], [m24], "o", color="#1F4E79", ms=6)
ax.annotate(f"  1.21", (design_tilt, m24), fontsize=9, color="#1F4E79",
            va="center")
ax.set_xlabel("panel tilt  (deg)")
ax.set_ylabel("climb margin  (45 N / drive load)")
ax.set_title("Climb-margin sensitivity to tilt and guide-wheel friction")
ax.set_xlim(0, 35)
ax.set_ylim(0.6, 2.6)
ax.grid(alpha=0.3)
ax.legend(loc="upper right", fontsize=8, framealpha=0.95)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig_tilt_margin.pdf"))
fig.savefig(os.path.join(HERE, "fig_tilt_margin.png"), dpi=150)
print("wrote fig_tilt_margin.pdf/.png")
print("critical tilts (margin=1):", {mu: round(c, 1) for mu, c in crit.items()})

# --------------------------------------------------------------------------
# (B) THREE-SCALE DEPLOYMENT SCALING
# --------------------------------------------------------------------------
# representative points inside the project's stated ranges:
#   commercial 50-500 kWp, residential 3-20 kWp, street-lamp 0.1-0.4 kWp
variants = [
    ("Commercial rooftop", 200.0),
    ("Residential rooftop", 9.9),   # the validated model point
    ("Street-lamp PV",      0.3),
]

rows = []
for name, kWp in variants:
    area = kWp * area_per_kWp
    water_event = L_per_m2 * area
    water_day = water_event / clean_interval_d
    water_yr = water_day * 365
    n_tiles = math.ceil(water_day / tile_water_Lday)
    pv_Wp = n_tiles * pv_Wp_per_tile
    tank_fills = water_event / tank_L
    clean_time_h = area / rate_m2h
    # units needed so the whole array is cleaned within one interval at field duty
    req_m2day = area / clean_interval_d
    n_units = max(1, math.ceil(req_m2day / unit_capacity_m2day))
    rows.append({
        "variant": name, "kWp": kWp, "area_m2": round(area, 1),
        "water_event_L": round(water_event, 2), "water_day_L": round(water_day, 2),
        "water_yr_L": round(water_yr, 0), "n_tiles": n_tiles,
        "dock_PV_Wp": round(pv_Wp, 0), "tank_fills": round(tank_fills, 1),
        "clean_time_h": round(clean_time_h, 2), "n_units": n_units,
    })

print("\n%-20s %6s %7s %8s %8s %7s %8s %7s %8s %6s" % (
    "variant", "kWp", "area", "L/evt", "L/day", "tiles", "PV Wp", "fills", "t_h", "units"))
for r in rows:
    print("%-20s %6.1f %7.1f %8.2f %8.2f %7d %8.0f %7.1f %8.2f %6d" % (
        r["variant"], r["kWp"], r["area_m2"], r["water_event_L"], r["water_day_L"],
        r["n_tiles"], r["dock_PV_Wp"], r["tank_fills"], r["clean_time_h"], r["n_units"]))

print(f"\nanchors: area/kWp={area_per_kWp:.3f} m2, tile={tile_water_Lday} L/day, "
      f"PV/tile={pv_Wp_per_tile:.1f} Wp, unit cap={unit_capacity_m2day:.0f} m2/day")

with open(os.path.join(HERE, "model_scaling_results.json"), "w") as f:
    json.dump({"critical_tilt_deg": {str(k): round(v, 2) for k, v in crit.items()},
               "margin_at_24_mu05": round(m24, 3),
               "anchors": {"area_per_kWp": area_per_kWp,
                           "tile_water_Lday": tile_water_Lday,
                           "pv_Wp_per_tile": pv_Wp_per_tile,
                           "unit_capacity_m2day": unit_capacity_m2day},
               "variants": rows}, f, indent=2)
print("wrote model_scaling_results.json")
