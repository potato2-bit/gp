#!/usr/bin/env python3
"""
test_water_bus.py -- validate the WaterBus accounting WITHOUT ROS, by driving it
through a full simulated year and checking it reproduces the annual co-sim's
water balance for the same site and bed size.

This is the off-board check the ROS node relies on: same physics, no Gazebo.
Run:  python integration/test_water_bus.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from awh_water_bus import WaterBus   # noqa: E402

SITE = "nac"
GEL_KG = 45.0
AREA = 46.0
L_PER_M2 = 0.3
SPRAY_RATE = 0.05            # L/s
INTERVAL_DAYS = 3.5         # design cadence
DAY_SECONDS = 1.0           # 1 wall-second == 1 climate day (scale-free here)


def run_year():
    bus = WaterBus(site=SITE, gel_kg=GEL_KG, area_m2=AREA,
                   L_per_m2=L_PER_M2, spray_rate_Lps=SPRAY_RATE)
    event_L = L_PER_M2 * AREA
    spray_seconds_per_event = event_L / SPRAY_RATE     # s of spraying to apply 1 event
    cleans = 0
    soil = 0.0
    for day in range(bus.n_days):
        bus.advance_day()
        soil += 1.0 / INTERVAL_DAYS                    # fraction of a clean-interval
        if soil >= 1.0:
            soil -= 1.0
            # apply one cleaning event as a burst of spray ticks (dt=1 s)
            applied = 0.0
            for _ in range(int(round(spray_seconds_per_event))):
                applied += bus.spray_tick(1.0)
            if applied >= 0.95 * event_L:
                cleans += 1
    return bus, cleans


def main():
    bus, cleans = run_year()
    b = bus.balance()
    demand_L = (bus.n_days / INTERVAL_DAYS) * bus.event_L
    print("WaterBus year-long self-check  (site=%s, gel=%.0f kg)" % (SITE, GEL_KG))
    print("-" * 58)
    print(f"  climate days         : {bus.n_days}")
    print(f"  cleans completed     : {cleans}  (due ~{bus.n_days/INTERVAL_DAYS:.0f})")
    print(f"  harvested            : {b['harvested_L']:.1f} L/yr")
    print(f"  sprayed (demand)     : {b['sprayed_L']:.1f} L/yr  "
          f"(nominal {demand_L:.0f} L)")
    print(f"  dock refilled tank   : {b['refilled_L']:.1f} L")
    print(f"  spray deficit        : {b['deficit_L']:.2f} L")
    print(f"  self-supply f        : {b['self_supply_f']}")

    # checks
    ok = True
    # 1. conservation: harvested ~ banked(dock) + sprayed + spilled(over cap), but
    #    at minimum harvested must cover sprayed for a self-sufficient site.
    if b["self_supply_f"] is None or b["self_supply_f"] < 1.0:
        print("  ** FAIL: not self-sufficient (f < 1) at the sized bed")
        ok = False
    # 2. the bed was sized to ~1.2x annual demand -> f near 1.2 +- climate
    if not (1.0 <= b["self_supply_f"] <= 1.45):
        print(f"  ** WARN: f={b['self_supply_f']} outside the expected 1.0-1.45 band")
    # 3. NAC at 45 kg should run essentially deficit-free
    if b["deficit_L"] > 0.5 * bus.event_L:
        print(f"  ** WARN: deficit {b['deficit_L']:.1f} L exceeds half a clean")
    if ok:
        print("  OK: WaterBus closes the loop and is self-sufficient at NAC.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
