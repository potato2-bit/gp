# AWH ↔ PVbot Integration — Work Log

## Goal
Integrate the AWH (atmospheric water harvesting) system with the PVbot Gazebo
simulation and run the analysis based on that integration.

## Project map (the two halves being bridged)
- **SUPPLY — `awh_sim/`**: solar-regenerated silica-gel AWH. Per-day water yield
  for the 1 m³ (750 kg) reference bed at six Egyptian sites lives in
  `awh_sim/results/annual_<site>.csv` (one adsorb-night/desorb-day cycle per day,
  driven by NASA POWER 2020 climate). The as-built thermoelectric (TEC) dock
  baseline comes from `output/nac_tec_robot_results.json`.
- **DEMAND — `gazebo/pvbot_description/`**: rail-guided robot sprays 0.3 L/m² per
  cleaning pass over a tilted PV array. Cleaning is soiling-triggered. Per-scale
  areas/water in `gazebo/pvbot_description/model_scaling_results.json`.
- **Visual AWH models — `gazebo/awh_description/`**: `awh_cube_world.sdf` (passive
  nested cube, residential/family) and `awh_world.sdf` (1 m³ forced-flow,
  commercial).

## The coupling
A dock reservoir is the bus between supply and demand. Each day the AWH adds its
climate-set yield; on a cleaning day the robot withdraws `L_per_m2 × area`. The
reservoir is clipped to a finite buffer. A clean the reservoir cannot cover is
deferred — the panel stays dirty, soiling keeps climbing, and the lost PV energy
is booked. Reported per site × scale: self-sufficiency factor
`f = annual supply / annual demand`, deferred-clean days and their PV-energy cost,
the minimum AWH size that drives deferrals to zero, harvesting+cleaning
electricity vs. the array's own output, and the PV energy cleaning recovers.

## Decision: TEC → silica-gel AWH as the robot's water source

### Sizing — the silica unit is small
- Residential demand ≈ 1,435 L/yr (3.94 L/day) — matches the design's 1,439 L/yr.
- Silica yield ≈ 38.6 L/kg-gel/yr at NAC; 25.5 at arid Benban.
- Sized bed (1.20× annual demand): ~44–46 kg at NAC/Delta, ~68 kg at Benban.
- Fits the ~0.4 m AWH cube (≈30–60 kg gel at 750 kg/m³). A sliver of the 750 kg /
  1 m³ feasibility bed in `awh_sim` (that big bed was the standalone feasibility
  study; the robot dock is right-sized).

### Energy — the real win
- TEC dock drew ~2,129 kWh/yr electrical (heat pump, SEC ≈ 1.45 kWh/L, COP 1.9).
- Silica regenerates with solar-thermal heat; electrical draw is just the fan:
  SEC_elec ≈ 0.11–0.17 kWh/kg → far less electricity for the same water.
- Total SEC ≈ 1.1–1.3 kWh/kg supplied free by the sun via the collector.
- Integrated AWH + robot electricity is only **~1.2–1.6 % of the array's output**
  and recovers **~7,400–8,900 kWh/yr** (residential 9.9 kWp) — the value of the
  water.

### Trade-offs
- Plus: far less electricity, no refrigerant, robust/repairable, CADET-validated;
  passive nested-cube option needs no fan (≳0.02 m/s natural convection keeps
  ~89–98 % of yield).
- Minus: water arrives in daily batches, not continuously, so tank buffering
  matters. The 3.6 L carriage tank ≈ one day's demand; a larger dock cistern
  smooths it.
- Sorbent bed + solar collector add mass/footprint vs. the TEC tile stack, but
  the dock is stationary so the 8 kg carriage budget is unaffected.

## Gazebo changes
- Drop the `awg_dock` model (TEC tiles/fins/fans/cold-plate) from
  `panel_world_tilt.sdf`; stand the silica unit in its place (dock pose ≈
  `-1.05 0 0`, bottom of the rail).
- Reuse `awh_cube_world.sdf` (nested cube → residential dock) and `awh_world.sdf`
  (1 m³ → commercial).

## Model resize + visualization request
- Resizing the silica unit: residential bed ~44–68 kg (~0.06–0.09 m³) stands in
  cleanly where the TEC dock was. `awh_description/make_cube_sdf.py` is
  parametric — regenerates the cube world at any tank level
  (`--water H --camera --out f.sdf`).
- Tank filling — already supported: `animate_fill.sh` sweeps water levels →
  `awh_fill.gif`, per-level frames (`frames/frame_00..09.png`),
  `awh_fill_empty/full.png`. Headless render: camera sensor + `<save>` through
  `gzserver` with `DISPLAY=:0` under WSLg; frames → GIF via PIL (MP4 via ffmpeg).
- Honest caveat — "water washing the robot": Gazebo Classic has no native
  fluid/particle simulation; per `COMPONENT_MAP.md` the spray and brush are static
  visuals ("no spinning roller joint, no fluid"). A literal water stream isn't
  producible. What is realistic and convincing for screenshots/video:
  - dock reservoir/tank level rising (real, parametric fill) and carriage tank
    draining per pass;
  - a spray visual — translucent fan/cone under the spray bar toggled on during
    cleaning strokes (`spray_on` already exists in `pvbot_coverage.py`);
  - a dirty→clean panel cue — swapping panel material/color from soiled to clean
    as the brush sweeps over it.

## Co-simulation engine (`integration/awh_pvbot_cosim.py`)
Daily time-stepping water + energy balance over the 366-day climate series at
6 sites × 3 scales. Two bugs found and fixed during the build:
1. **Gel-bed sizing absurdity (55,000–93,000 kg).** Root cause: per-day `m_w_kg`
   in `annual_<site>.csv` is for a single small design-point column (area
   0.00785 m²), while `annual_summary.csv` scales the 750 kg bed by replicating
   modules. Fix: take the annual per-kg yield from the summary
   (`water_kg_yr / 750`) as the magnitude and use the per-day column only as the
   normalised daily **shape** (sums to 1).
2. **Discrete cleaning cadence rounding 3.5 → 4 days.** Fix: carry the soiling
   remainder (`acc -= threshold` instead of `acc = 0`) → true mean 3.5-day
   cadence, reproducing the design's 1,439 L/yr.

### Config (traceable constants)
- `L_per_m2 = 0.3` (rail_guided_design.json), `gel_bed_ref_kg = 750`.
- Soiling: `1.0 %/day` loss (Benban-class desert), clean at `3.5 %` →
  3.5-day interval. `design_margin = 1.20`, `buffer_days = 7`.
- `PR = 0.80`; per-site PSH 5.3–6.4.
- `E_event_Wh_res = 73.97` (nac_tec_robot_results mechanics), scaled by area.

## Results (residential rooftop, 9.9 kWp, 46 m²)
| Site | demand L/yr | sized gel kg | min kg (0 deficit) | f | deferred d | TEC tiles | parasitic % |
|---|---|---|---|---|---|---|---|
| Benban (Aswan) | 1435 | 67.6 | 76.5 | 1.20 | 6 | 57 | 1.63 |
| Mansoura | 1435 | 44.5 | 42.0 | 1.20 | 0 | 38 | 1.32 |
| New Alamein | 1435 | 46.4 | 42.1 | 1.20 | 0 | 39 | 1.30 |
| Hurghada | 1435 | 58.0 | 60.9 | 1.20 | 2 | 49 | 1.43 |
| Siwa | 1435 | 52.0 | 58.2 | 1.20 | 5 | 44 | 1.35 |
| New Admin. Capital | 1435 | 44.6 | 45.5 | 1.20 | 1 | 38 | 1.23 |

### Self-validations
- demand 1,435 L/yr ≈ design 1,439 L/yr.
- gel bed 44–68 kg fits the ~0.4 m cube.
- TEC tiles at NAC = 38 = the as-built 38-tile dock.
- Commercial gel bed ≈ 0.9–1.5 m³ ≈ the "1 m³ industrial unit".
- Street-lamp = 2 tiles = `model_scaling` n_tiles.

### Key finding — seasonal spell, not annual average, is binding
At an annual margin of f = 1.20, arid sites still defer cleans (Benban 6,
Siwa 5, Hurghada 2, NAC 1) because a summer low-RH spell drains the reservoir.
So `min_gel_kg` for zero deferral exceeds the annual-sized bed in arid sites
(Benban needs 76.5 vs 67.6 kg sized). Humid-Delta sites (Mansoura, New Alamein)
have surplus: 42 kg suffices vs 44–46 kg sized.

### Scale invariance
Parasitic load (% of array output) is ~constant across street-lamp / residential
/ commercial for a given site, because supply energy and PV output both scale
with size.

## Outputs
- `integration/awh_pvbot_cosim.py` — co-simulation engine.
- `integration/results/integration_sweep.csv` — full 6×3 sweep.
- `integration/results/integration_summary.json` — residential headline.
- `integration/results/reservoir_timeseries.npz` — daily reservoir + clean flags.
- `integration/make_figures.py` — figure generator.
- `integration/figures/` (PNG + PDF):
  - `fig_reservoir_year` — coupled dock reservoir level vs day, 6 sites.
  - `fig_sizing` — sized bed vs bed needed for zero deferral, per site.
  - `fig_supply_demand` — annual AWH supply vs cleaning demand + deferred cleans.
  - `fig_energy_balance` — parasitic harvest+clean load vs array output + recovered.
  - `fig_site_detail` — Benban: reservoir, cleaning draws, climate driver.
  - `fig_scale_invariant` — same parasitic % across the three scales.

## Execution note
WSL (where Gazebo lives) was stopped. Starting WSL, regenerating the resized
world, running the sweep, and capturing frames/video remains to be done.
```
