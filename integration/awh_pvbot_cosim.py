#!/usr/bin/env python3
"""
awh_pvbot_cosim.py -- couples the AWH water-supply model to the PV-cleaning
robot's water demand and runs a daily, climate-driven balance over a year.

WHAT THIS INTEGRATES
--------------------
Two halves of the project that until now lived apart:

  SUPPLY  awh_sim/ -- the solar-regenerated silica-gel AWH. Its per-day water
          yield for the 1 m3 (750 kg) reference bed at six Egyptian sites lives
          in awh_sim/results/annual_<site>.csv (one adsorb-night/desorb-day
          cycle per day, driven by NASA POWER 2020 climate). Per-kg yield scales
          a bed of any mass. The thermoelectric (TEC) dock used in the built
          robot is carried as the as-built baseline from
          output/nac_tec_robot_results.json.

  DEMAND  gazebo/pvbot_description/ -- the rail-guided robot sprays 0.3 L/m2 per
          cleaning pass over a tilted PV array. Cleaning is triggered by soiling:
          dust accumulates, the array loses power, and the robot cleans when the
          loss crosses a threshold. That sets when -- and how much -- water is
          drawn. Areas and per-event water by scale come from
          gazebo/pvbot_description/model_scaling_results.json.

THE COUPLING
------------
A dock reservoir is the bus between them. Each day the AWH adds its climate-set
yield; on a cleaning day the robot withdraws L_per_m2 x area. The reservoir is
clipped to a finite buffer. If it cannot cover a due clean, that clean is
deferred -- the panel stays dirty, soiling keeps climbing, and the lost PV
energy is booked. The model reports, per site x scale:
  * self-sufficiency factor f = annual AWH supply / annual cleaning demand
  * deficit (deferred-clean) days and the PV energy they cost
  * the minimum AWH size that drives deficits to zero
  * the electrical energy of harvesting + cleaning vs. the array's own output
  * the PV energy the cleaning recovers, i.e. what the water is worth

Run:  python integration/awh_pvbot_cosim.py
Out:  integration/results/*.csv, integration/results/integration_summary.json
"""
import json
import os
import math
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
AWH = os.path.join(ROOT, "awh_sim")
GZ = os.path.join(ROOT, "gazebo", "pvbot_description")
OUT = os.path.join(ROOT, "output")
RES = os.path.join(HERE, "results")
os.makedirs(RES, exist_ok=True)

# ---------------------------------------------------------------------------
# CONFIG -- every constant traces to a model file or a cited value
# ---------------------------------------------------------------------------
SITES = ["aswan_benban", "mansoura", "new_alamein", "hurghada", "siwa", "nac"]
SITE_LABEL = {
    "aswan_benban": "Benban (Aswan)", "mansoura": "Mansoura",
    "new_alamein": "New Alamein", "hurghada": "Hurghada",
    "siwa": "Siwa", "nac": "New Admin. Capital",
}

L_PER_M2 = 0.3          # L per cleaning event (rail_guided_design.json)
GEL_BED_KG = 750.0      # reference bed mass behind annual_<site>.csv (awh_sim)

# Soiling model (arid Egypt). Loss accrues linearly; the robot cleans when the
# accumulated loss crosses CLEAN_THRESHOLD. The default rate is set so the
# residential interval lands on the design's 3.5 days, tying the cadence to a
# physical soiling rate rather than a bare assumption.
#   interval = threshold / soil_rate  ->  3.5 % / 1.0 %/day = 3.5 day
SOIL_RATE_PCT_DAY = 1.0   # %/day power loss from dust (Benban-class desert)
CLEAN_THRESHOLD_PCT = 3.5  # % loss that triggers a clean
DESIGN_MARGIN = 1.20      # size the AWH bed 20 % over annual demand
BUFFER_DAYS = 7.0         # dock reservoir holds ~a week of demand (household cistern)

# Economics / energy context
PR = 0.80                 # PV performance ratio (DC->AC, temp, wiring)
PSH = {                   # peak-sun-hours/day per site (NASA POWER class)
    "aswan_benban": 6.4, "mansoura": 5.3, "new_alamein": 5.6,
    "hurghada": 6.3, "siwa": 6.0, "nac": 5.7,
}

# Robot energy per cleaning event by scale. Residential is anchored to
# model_calcs (E_per_panel x panels) and the others scale with array area.
E_EVENT_WH_RES = 73.97    # Wh per residential clean (nac_tec_robot_results mechanics)


def load_scales():
    """Per-scale geometry from the Gazebo scaling study."""
    with open(os.path.join(GZ, "model_scaling_results.json")) as f:
        sc = json.load(f)
    scales = {}
    for v in sc["variants"]:
        scales[v["variant"]] = {
            "kWp": v["kWp"], "area_m2": v["area_m2"],
            "event_L": v["water_event_L"], "n_tiles": v["n_tiles"],
        }
    return scales


def load_site_yield(site):
    """Per-day climate drivers and the normalised daily yield SHAPE from
    awh_sim/results/annual_<site>.csv. The raw m_w_kg there is a single small
    design-point column; the 750 kg bed is realised by replicating modules, so
    the absolute annual yield comes from annual_summary (water_kg_yr / 750 kg
    -> L per kg-gel per year). Here we keep only the day-to-day SHAPE (sums to
    1) and let the per-kg annual figure set the magnitude."""
    df = pd.read_csv(os.path.join(AWH, "results", f"annual_{site}.csv"))
    tot = df["m_w_kg"].sum()
    df["shape"] = df["m_w_kg"] / tot if tot else 1.0 / len(df)   # dimensionless
    return df


def annual_yield_per_kg(site, econ):
    """L of water per kg of silica gel per year at this site (annual_summary)."""
    return float(econ.loc[site, "water_kg_yr"]) / GEL_BED_KG


def load_site_econ():
    """Per-site electric SEC and annual silica yield from the summary table."""
    s = pd.read_csv(os.path.join(AWH, "results", "annual_summary.csv"))
    s = s.set_index("site")
    return s


def tec_dock_per_tile_Lday():
    """As-built TEC dock yield, L/day per TEC1-12706 tile (NAC reference)."""
    with open(os.path.join(OUT, "nac_tec_robot_results.json")) as f:
        d = json.load(f)
    return d["per_tile"]["water_gday"] / 1000.0


# ---------------------------------------------------------------------------
# Cleaning schedule from the soiling model
# ---------------------------------------------------------------------------
def cleaning_days(n_days, soil_rate, threshold):
    """Return the set of day indices on which the robot cleans. Soiling builds
    at soil_rate %/day; a clean fires (and resets the dust) when it reaches the
    threshold. Returns days and the implied interval."""
    interval = threshold / soil_rate
    days, acc = [], 0.0
    for d in range(n_days):
        acc += soil_rate
        if acc >= threshold:
            days.append(d)
            acc -= threshold          # carry the remainder -> true mean cadence
    return days, interval


# ---------------------------------------------------------------------------
# Daily reservoir co-simulation
# ---------------------------------------------------------------------------
def simulate(site, scale_name, scale, gel_mass_kg, econ,
             soil_rate=SOIL_RATE_PCT_DAY, threshold=CLEAN_THRESHOLD_PCT):
    """Step the dock reservoir day by day for one site x scale x AWH size.

    Reservoir(d) = clip(Reservoir(d-1) + supply(d) - withdraw(d), 0, cap).
    A due clean that the reservoir cannot cover is deferred; soiling continues
    and the lost PV energy that day is accumulated until the next successful
    clean."""
    yd = load_site_yield(site)
    n = len(yd)
    ann_per_kg = annual_yield_per_kg(site, econ)     # L/kg-gel/yr
    supply = gel_mass_kg * ann_per_kg * yd["shape"].to_numpy()  # L/day, sized bed

    event_L = L_PER_M2 * scale["area_m2"]
    demand_Lday = event_L * soil_rate / threshold    # mean daily draw
    cap = max(1.5 * event_L, BUFFER_DAYS * demand_Lday)

    clean_set, interval = cleaning_days(n, soil_rate, threshold)
    clean_flag = np.zeros(n, dtype=bool)
    clean_flag[clean_set] = True

    # PV context for energy bookkeeping
    pv_kWh_yr = scale["kWp"] * PSH[site] * 365.0 * PR
    e_event_wh = E_EVENT_WH_RES * (scale["area_m2"] / 46.0)  # scale with area

    reservoir = np.zeros(n)
    level = min(cap, supply[0])           # start with one day of harvest
    deferred = 0
    soil_since_clean = 0.0                # % loss carried while waiting
    energy_lost_kWh = 0.0                 # PV energy lost to deferred cleans
    cleans_done = 0
    withdraw_total = 0.0

    for d in range(n):
        level = min(cap, level + supply[d])
        soil_since_clean += soil_rate
        if clean_flag[d]:
            if level >= event_L:
                level -= event_L
                withdraw_total += event_L
                cleans_done += 1
                soil_since_clean = 0.0
            else:
                deferred += 1
                # one extra day at the standing soiling loss before recovery
                frac_loss = soil_since_clean / 100.0
                energy_lost_kWh += pv_kWh_yr / 365.0 * frac_loss * interval
        reservoir[d] = level

    supply_Lyr = float(supply.sum())
    demand_Lyr = event_L * len(clean_set)
    f_self = supply_Lyr / demand_Lyr if demand_Lyr else float("inf")

    sec_elec = float(econ.loc[site, "sec_elec_kWh_kg"])  # kWh per kg water
    awh_elec_kWh = supply_Lyr * sec_elec
    robot_elec_kWh = cleans_done * e_event_wh / 1000.0
    parasitic_kWh = awh_elec_kWh + robot_elec_kWh
    parasitic_frac = parasitic_kWh / pv_kWh_yr if pv_kWh_yr else float("nan")

    # Energy the cleaning recovers: without cleaning the array would sit at the
    # mean standing soiling loss; cleaning holds it near the half-interval mean.
    loss_uncleaned = min(0.5, soil_rate / 100.0 * 180)   # ~6-month dust cap, fraction
    loss_cleaned = (soil_rate / 100.0) * interval / 2.0  # mean sawtooth loss
    energy_recovered_kWh = pv_kWh_yr * (loss_uncleaned - loss_cleaned)

    return {
        "site": site, "scale": scale_name, "gel_kg": gel_mass_kg,
        "interval_days": interval, "cleans_due": len(clean_set),
        "cleans_done": cleans_done, "deferred_days": deferred,
        "event_L": event_L, "demand_Lyr": demand_Lyr,
        "supply_Lyr": supply_Lyr, "self_supply_f": f_self,
        "reservoir_cap_L": cap, "reservoir_min_L": float(reservoir.min()),
        "reservoir_mean_L": float(reservoir.mean()),
        "awh_elec_kWh_yr": awh_elec_kWh, "robot_elec_kWh_yr": robot_elec_kWh,
        "parasitic_kWh_yr": parasitic_kWh, "parasitic_frac": parasitic_frac,
        "pv_kWh_yr": pv_kWh_yr, "energy_lost_kWh_yr": energy_lost_kWh,
        "energy_recovered_kWh_yr": energy_recovered_kWh,
        "_reservoir": reservoir, "_supply": supply, "_clean_flag": clean_flag,
    }


def size_gel_bed(site, scale, econ, margin=DESIGN_MARGIN,
                 soil_rate=SOIL_RATE_PCT_DAY, threshold=CLEAN_THRESHOLD_PCT):
    """Silica-gel bed mass (kg) sized to cover annual demand x margin."""
    yd = load_site_yield(site)
    ann_per_kg = annual_yield_per_kg(site, econ)              # L/kg-gel/yr
    clean_set, _ = cleaning_days(len(yd), soil_rate, threshold)
    demand_Lyr = L_PER_M2 * scale["area_m2"] * len(clean_set)
    return demand_Lyr * margin / ann_per_kg


def min_size_zero_deficit(site, scale_name, scale, econ):
    """Smallest bed mass (kg) that yields zero deferred cleans, by bisection."""
    lo, hi = 0.01, 5000.0
    # ensure hi is enough
    for _ in range(40):
        r = simulate(site, scale_name, scale, hi, econ)
        if r["deferred_days"] == 0:
            break
        hi *= 1.5
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        r = simulate(site, scale_name, scale, mid, econ)
        if r["deferred_days"] == 0:
            hi = mid
        else:
            lo = mid
    return hi


# ---------------------------------------------------------------------------
# Main sweep
# ---------------------------------------------------------------------------
def main():
    scales = load_scales()
    econ = load_site_econ()
    tile_Lday = tec_dock_per_tile_Lday()

    rows = []
    timeseries = {}        # (site, scale) -> reservoir array, for figures
    for scale_name, scale in scales.items():
        for site in SITES:
            gel = size_gel_bed(site, scale, econ)
            r = simulate(site, scale_name, scale, gel, econ)
            r["min_gel_kg_zero_deficit"] = min_size_zero_deficit(
                site, scale_name, scale, econ)
            # as-built TEC dock comparison: tiles to meet demand at this site
            # (yield scaled from the NAC per-tile figure by the silica supply
            #  ratio site/NAC, a first-order climate transfer)
            site_ratio = (float(econ.loc[site, "water_kg_yr"]) /
                          float(econ.loc["nac", "water_kg_yr"]))
            tec_Lday_site = tile_Lday * site_ratio
            r["tec_tiles_for_demand"] = math.ceil(
                (r["demand_Lyr"] / 365.0) / tec_Lday_site)
            timeseries[(site, scale_name)] = {
                "reservoir": r.pop("_reservoir"),
                "supply": r.pop("_supply"),
                "clean_flag": r.pop("_clean_flag"),
            }
            rows.append(r)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "integration_sweep.csv"), index=False)

    # lightweight inputs for the live ROS2 water-bus node (numpy/csv only):
    # the per-day yield SHAPE (sums to 1) and the per-kg annual yield, so the
    # node can build supply = gel_kg * per_kg[site] * shape[site][doy].
    shape_tbl = {"doy": load_site_yield(SITES[0])["doy"].to_numpy()}
    per_kg = {}
    for site in SITES:
        shape_tbl[site] = load_site_yield(site)["shape"].to_numpy()
        per_kg[site] = annual_yield_per_kg(site, econ)
    pd.DataFrame(shape_tbl).to_csv(
        os.path.join(RES, "site_yield_shape.csv"), index=False)
    with open(os.path.join(RES, "site_yield_per_kg.json"), "w") as f:
        json.dump(per_kg, f, indent=2)

    # save residential time series for the headline figure
    np.savez(
        os.path.join(RES, "reservoir_timeseries.npz"),
        **{f"{s}": timeseries[(s, "Residential rooftop")]["reservoir"]
           for s in SITES},
        **{f"clean_{s}": timeseries[(s, "Residential rooftop")]["clean_flag"]
           for s in SITES},
    )

    # headline JSON
    res = df[df.scale == "Residential rooftop"].set_index("site")
    summary = {
        "config": {
            "L_per_m2": L_PER_M2, "soil_rate_pct_day": SOIL_RATE_PCT_DAY,
            "clean_threshold_pct": CLEAN_THRESHOLD_PCT,
            "design_margin": DESIGN_MARGIN, "buffer_days": BUFFER_DAYS,
            "gel_bed_ref_kg": GEL_BED_KG,
        },
        "residential": {
            site: {
                "interval_days": round(float(res.loc[site, "interval_days"]), 2),
                "demand_Lyr": round(float(res.loc[site, "demand_Lyr"]), 1),
                "gel_kg_sized": round(float(res.loc[site, "gel_kg"]), 1),
                "min_gel_kg_zero_deficit": round(
                    float(res.loc[site, "min_gel_kg_zero_deficit"]), 1),
                "self_supply_f": round(float(res.loc[site, "self_supply_f"]), 3),
                "deferred_days": int(res.loc[site, "deferred_days"]),
                "tec_tiles_for_demand": int(res.loc[site, "tec_tiles_for_demand"]),
                "parasitic_frac": round(float(res.loc[site, "parasitic_frac"]), 5),
                "energy_recovered_kWh_yr": round(
                    float(res.loc[site, "energy_recovered_kWh_yr"]), 1),
            } for site in SITES
        },
    }
    with open(os.path.join(RES, "integration_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # console report
    print("=" * 74)
    print(" AWH <-> PVbot INTEGRATION -- residential rooftop (9.9 kWp, 46 m2)")
    print("=" * 74)
    print(f" soiling {SOIL_RATE_PCT_DAY}%/day, clean at {CLEAN_THRESHOLD_PCT}% "
          f"-> {res.iloc[0]['interval_days']:.1f}-day interval")
    print(f"{'site':<20}{'demand':>9}{'gel kg':>8}{'min kg':>8}"
          f"{'f':>7}{'defer':>7}{'TEC til':>8}")
    for site in SITES:
        r = res.loc[site]
        print(f"{SITE_LABEL[site]:<20}{r['demand_Lyr']:>8.0f}"
              f"{r['gel_kg']:>8.1f}{r['min_gel_kg_zero_deficit']:>8.1f}"
              f"{r['self_supply_f']:>7.2f}{int(r['deferred_days']):>7d}"
              f"{int(r['tec_tiles_for_demand']):>8d}")
    print("-" * 74)
    print(" parasitic load (AWH elec + robot) as % of array output:")
    for site in SITES:
        print(f"   {SITE_LABEL[site]:<20}{res.loc[site,'parasitic_frac']*100:>6.2f} %"
              f"   recovers {res.loc[site,'energy_recovered_kWh_yr']:>7.0f} kWh/yr")
    print("\nwrote integration_sweep.csv, integration_summary.json, "
          "reservoir_timeseries.npz")
    return df, summary


if __name__ == "__main__":
    main()
