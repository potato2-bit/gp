# AWH ↔ PVbot integration

Couples the two simulations the project had kept apart:

- **Supply** — `awh_sim/`, the solar-regenerated silica-gel atmospheric water
  harvester. Per-day water yield for the 750 kg reference bed at six Egyptian
  sites, driven by NASA POWER (2020) climate. The as-built thermoelectric (TEC)
  dock (`output/nac_tec_robot_results.json`) is carried as a baseline.
- **Demand** — `gazebo/pvbot_description/`, the rail-guided cleaning robot that
  sprays 0.3 L/m² per pass over a 24° PV panel.

They are joined by a **dock reservoir**: each climate day the AWH banks its
yield; each cleaning pass draws from it. A daily, year-long co-simulation over
the real climate series answers the question the two halves only assumed:
**can the robot harvest the water it needs to clean the array that powers it?**

## Headline result (residential, 9.9 kWp, 46 m²)

| Site | Demand (L/yr) | Sized bed (kg) | Min kg (0 deficit) | Deferred cleans | TEC tiles | Parasitic (% array) |
|---|---|---|---|---|---|---|
| Benban (Aswan) | 1435 | 67.6 | **76.5** | 6 | 57 | 1.64 |
| Mansoura | 1435 | 44.5 | 42.0 | 0 | 38 | 1.32 |
| New Alamein | 1435 | 46.4 | 42.1 | 0 | 39 | 1.30 |
| Hurghada | 1435 | 58.0 | 60.9 | 2 | 49 | 1.43 |
| Siwa | 1435 | 52.0 | 58.2 | 5 | 44 | 1.35 |
| New Admin. Capital | 1435 | 44.6 | 45.5 | 1 | **38** | 1.23 |

Three findings that only appear once supply and demand share a clock:

1. **The loop closes everywhere** at residential scale with a 42–77 kg silica
   bed — a canister that fits the 0.4 m dock cube. The TEC-tile column lands on
   **38 tiles at NAC**, exactly the as-built dock — a validation against the
   hardware design.
2. **The constraint is the summer spell, not the annual average.** Sizing to a
   20% annual surplus is *not* enough in arid sites: Benban still defers 6 cleans
   because a low-humidity summer stretch (days ~120–240) drains the reservoir.
   Humid Delta sites ride through with margin. Size to the worst spell.
3. **Self-supply is scale-invariant** and the parasitic load is tiny: harvesting
   + cleaning draw **1.2–1.6 %** of the array's own output while recovering
   thousands of kWh/yr in avoided soiling loss.

## Files

| file | what it is |
|---|---|
| `awh_pvbot_cosim.py` | the coupled annual water+energy balance (6 sites × 3 scales) → `results/` |
| `make_figures.py` | the six analysis figures → `figures/` |
| `awh_water_bus.py` | **live ROS 2 coupling** — subscribes to `spray_on`, banks AWH harvest, drains/refills tank, publishes the balance. Testable `WaterBus` core, no ROS dependency. |
| `test_water_bus.py` | off-board year-long self-check of `WaterBus` (no Gazebo) |
| `run_integrated_demo.sh` | brings the live coupling up in Gazebo + ROS 2 (WSL) |
| `build_demo.py` | writes the integrated-world SDFs + renders the demo (screenshots, GIF) |
| `make_integrated_world.py` | parametric integrated-world SDF generator |
| `../gazebo/awh_description/make_awh_dock_sdf.py` | the family AWH cube **resized** to the residential need (~45 kg) on the dock plinth |
| `AWH_PVBOT_INTEGRATION.tex` / `.pdf` | the full analysis report (6 pp) |
| `INTEGRATION_LOG.md` | running log of how the integration was built |

## Reproduce

```bash
python integration/awh_pvbot_cosim.py      # coupled annual balance -> results/
python integration/make_figures.py         # figures -> figures/
python integration/test_water_bus.py        # WaterBus self-check (NAC: f=1.21, 3.8 L deficit)
python integration/build_demo.py           # integrated-world SDFs + demo frames/GIF
bash    integration/run_integrated_demo.sh  # live Gazebo+ROS coupling (in WSL)
```

## Honesty notes

- Gazebo Classic has no fluid solver: the **tank fill is real geometry** (water
  column = reservoir level), the **spray is a visual cue**.
- Soiling is a single 1 %/day rate with a 3.5 % clean threshold — reproduces the
  design cadence, defensible for desert Egypt, but real soiling is episodic.
- The recovered-energy figure compares against a never-cleaned panel saturating
  at ~50 % loss, so it is an **upper bound** on the value of cleaning.
- The silica daily *shape* comes from the per-day design-point column; the
  *magnitude* from the replicated-module annual summary — which is why the bed
  sizing is sane (tens of kg, not tonnes).
