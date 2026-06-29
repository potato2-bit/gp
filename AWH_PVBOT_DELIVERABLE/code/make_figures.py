#!/usr/bin/env python3
"""
make_figures.py -- figures for the AWH <-> PVbot integration analysis.
Reads integration/results/ (written by awh_pvbot_cosim.py) and writes
publication PNG+PDF to integration/figures/.

  fig_reservoir_year   coupled dock-reservoir level vs day, 6 sites (residential)
  fig_sizing           sized bed vs the size needed for zero deficit, per site
  fig_supply_demand    annual AWH supply vs cleaning demand + deferred cleans
  fig_energy_balance    parasitic harvest+clean load vs array output + recovered
  fig_site_detail      one site: supply, reservoir, and cleaning draws over a year
  fig_scale_invariant  the same self-supply across the three deployment scales
"""
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 200, "font.size": 10,
    "axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
    "figure.constrained_layout.use": True,
})

SITES = ["aswan_benban", "mansoura", "new_alamein", "hurghada", "siwa", "nac"]
LBL = {"aswan_benban": "Benban (Aswan)", "mansoura": "Mansoura",
       "new_alamein": "New Alamein", "hurghada": "Hurghada",
       "siwa": "Siwa", "nac": "New Admin. Capital"}
COL = {"aswan_benban": "#c0392b", "mansoura": "#2471a3", "new_alamein": "#27ae60",
       "hurghada": "#e67e22", "siwa": "#8e44ad", "nac": "#16a085"}

df = pd.read_csv(os.path.join(RES, "integration_sweep.csv"))
ts = np.load(os.path.join(RES, "reservoir_timeseries.npz"))
res = df[df.scale == "Residential rooftop"].set_index("site")


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"))
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    plt.close(fig)
    print("wrote", name)


# 1 -- coupled reservoir level vs day, all sites (residential) --------------
fig, ax = plt.subplots(figsize=(8.2, 4.2))
for s in SITES:
    lvl = ts[s]
    ax.plot(np.arange(len(lvl)), lvl, color=COL[s], lw=1.4, label=LBL[s])
    cap = float(res.loc[s, "reservoir_cap_L"])
ax.axhline(float(res.loc["nac", "event_L"]), color="0.4", ls="--", lw=1,
           label="one clean (%.1f L)" % float(res.loc["nac", "event_L"]))
ax.set_xlabel("day of year")
ax.set_ylabel("dock reservoir level (L)")
ax.set_title("Coupled AWH dock reservoir over the year — residential rooftop "
             "(46 m², 3.5-day cleaning)")
ax.set_xlim(0, len(ts[SITES[0]]) - 1)
ax.legend(ncol=2, fontsize=8, loc="upper right")
save(fig, "fig_reservoir_year")


# 2 -- sizing: bed sized to margin vs bed for zero deficit ------------------
fig, ax = plt.subplots(figsize=(7.6, 4.0))
x = np.arange(len(SITES))
sized = [res.loc[s, "gel_kg"] for s in SITES]
needed = [res.loc[s, "min_gel_kg_zero_deficit"] for s in SITES]
ax.bar(x - 0.2, sized, 0.4, label="sized to 1.20× annual demand",
       color="#5dade2")
ax.bar(x + 0.2, needed, 0.4, label="needed for zero deferred cleans",
       color="#c0392b")
for i, s in enumerate(SITES):
    d = int(res.loc[s, "deferred_days"])
    if d:
        ax.annotate(f"{d} deferred", (i - 0.2, sized[i]), ha="center",
                    va="bottom", fontsize=7.5, color="#7b241c")
ax.set_xticks(x)
ax.set_xticklabels([LBL[s] for s in SITES], rotation=20, ha="right", fontsize=8)
ax.set_ylabel("silica-gel bed mass (kg)")
ax.set_title("Sizing the on-robot AWH bed: annual margin vs. worst-spell demand")
ax.legend(fontsize=8)
save(fig, "fig_sizing")


# 3 -- supply vs demand + deferred ------------------------------------------
fig, (axa, axb) = plt.subplots(1, 2, figsize=(9.4, 4.0),
                               gridspec_kw={"width_ratios": [3, 2]})
sup = [res.loc[s, "supply_Lyr"] for s in SITES]
dem = [res.loc[s, "demand_Lyr"] for s in SITES]
axa.bar(x - 0.2, sup, 0.4, label="AWH supply (sized bed)", color="#27ae60")
axa.bar(x + 0.2, dem, 0.4, label="cleaning demand", color="#34495e")
axa.set_xticks(x)
axa.set_xticklabels([LBL[s] for s in SITES], rotation=20, ha="right", fontsize=8)
axa.set_ylabel("water (L/yr)")
axa.set_title("Annual water: AWH supply vs. cleaning demand")
axa.legend(fontsize=8)
f = [res.loc[s, "self_supply_f"] for s in SITES]
defr = [res.loc[s, "deferred_days"] for s in SITES]
axb.bar(x, defr, 0.6, color=[COL[s] for s in SITES])
axb.set_xticks(x)
axb.set_xticklabels([LBL[s] for s in SITES], rotation=20, ha="right", fontsize=8)
axb.set_ylabel("deferred cleans (days/yr)")
axb.set_title("Cleans the bed could not cover\n(all sites at annual f = 1.20)")
axb.yaxis.set_major_locator(MaxNLocator(integer=True))
save(fig, "fig_supply_demand")


# 4 -- energy balance: parasitic load vs array output, + recovered ----------
fig, ax = plt.subplots(figsize=(8.0, 4.2))
awh = np.array([res.loc[s, "awh_elec_kWh_yr"] for s in SITES])
rob = np.array([res.loc[s, "robot_elec_kWh_yr"] for s in SITES])
pv = np.array([res.loc[s, "pv_kWh_yr"] for s in SITES])
rec = np.array([res.loc[s, "energy_recovered_kWh_yr"] for s in SITES])
ax.bar(x, awh, 0.5, label="AWH harvesting (elec)", color="#2980b9")
ax.bar(x, rob, 0.5, bottom=awh, label="robot cleaning (elec)", color="#8e44ad")
ax.plot(x, rec, "o-", color="#27ae60", lw=1.6, ms=6,
        label="PV energy recovered by cleaning")
for i, s in enumerate(SITES):
    ax.annotate(f"{res.loc[s,'parasitic_frac']*100:.2f}% of array",
                (i, (awh[i] + rob[i])), ha="center", va="bottom",
                fontsize=7, color="#1b2631")
ax.set_xticks(x)
ax.set_xticklabels([LBL[s] for s in SITES], rotation=20, ha="right", fontsize=8)
ax.set_ylabel("electrical energy (kWh/yr)")
ax.set_title("Energy: AWH+robot draw ~1.2–1.6% of array output,\n"
             "recover thousands of kWh/yr in avoided soiling loss")
ax.set_yscale("log")
ax.legend(fontsize=8, loc="center right")
save(fig, "fig_energy_balance")


# 5 -- one site detail: supply, reservoir, cleaning draws -------------------
site = "aswan_benban"   # the hardest (arid) — shows the seasonal deficit
lvl = ts[site]
sup = ts[f"_supply_{site}"] if f"_supply_{site}" in ts else None
clean = ts[f"clean_{site}"]
days = np.arange(len(lvl))
fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.2, 5.2), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
a1.plot(days, lvl, color=COL[site], lw=1.5, label="reservoir level")
a1.axhline(float(res.loc[site, "event_L"]), color="0.4", ls="--", lw=1,
           label="one clean (%.1f L)" % float(res.loc[site, "event_L"]))
cd = days[clean.astype(bool)]
a1.plot(cd, np.full_like(cd, float(res.loc[site, "event_L"]), dtype=float),
        "v", color="#7b241c", ms=4, label="cleaning draw")
a1.set_ylabel("reservoir (L)")
a1.set_title(f"{LBL[site]} — supply, storage and cleaning draws over the year")
a1.legend(fontsize=8, loc="upper right", ncol=2)
# daily supply from the shape * sized bed (recompute lightly here)
yd = pd.read_csv(os.path.join(HERE, "..", "awh_sim", "results",
                              f"annual_{site}.csv"))
a2.plot(days, yd["RH_ads_pct"], color="#2471a3", lw=1.0, label="night RH (%)")
a2b = a2.twinx()
a2b.plot(days, yd["T_ads_C"], color="#e67e22", lw=1.0, label="night T (°C)")
a2.set_ylabel("RH (%)", color="#2471a3")
a2b.set_ylabel("T (°C)", color="#e67e22")
a2.set_xlabel("day of year")
a2.set_title("Climate driver behind the supply (low summer RH drains the dock)")
save(fig, "fig_site_detail")


# 6 -- scale invariance ------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.4, 4.0))
scales = ["Street-lamp PV", "Residential rooftop", "Commercial rooftop"]
markers = {"Street-lamp PV": "o", "Residential rooftop": "s",
           "Commercial rooftop": "^"}
for sc in scales:
    sub = df[df.scale == sc].set_index("site")
    ax.plot(range(len(SITES)), [sub.loc[s, "parasitic_frac"] * 100 for s in SITES],
            marker=markers[sc], lw=1.4, label=sc)
ax.set_xticks(range(len(SITES)))
ax.set_xticklabels([LBL[s] for s in SITES], rotation=20, ha="right", fontsize=8)
ax.set_ylabel("parasitic load (% of array output)")
ax.set_title("Self-supply is scale-invariant: the same % across all three scales")
ax.legend(fontsize=8)
save(fig, "fig_scale_invariant")

print("\nall figures in", FIG)
