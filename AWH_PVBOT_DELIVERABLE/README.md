# AWH ↔ PVbot integration — complete deliverable

Everything built in this session, in one self-contained folder: the coupled
simulation that joins the **atmospheric water harvester (AWH)** to the
**PV-cleaning robot**, the analysis, the live ROS 2 coupling, the report, and a
rendered video + labelled multi-view screenshots of the integrated simulation.

## ▶ Watch the simulation first

**`figures/awh_pvbot_sim.mp4`** (and `.gif`) — the integrated loop, ~7 s:

1. **AWH harvesting (fast-forward)** — the solar-desiccant dock fills its 27.6 L
   tank over **~5 nights**. The fill rate is the **real climate-driven harvest**
   from the co-simulation (NAC: ~4.7 L/night for a 45 kg silica bed), so the
   water column climbs night by night — the HUD ticks "night 1, 2, 3 …" with the
   litres harvested each night. Column height = the actual reservoir level.
2. **Cleaning wash** — the carriage descends the 24° panel, the spray fan plays
   on the glass, the panel turns dust-tan → PV-blue behind the brush, and the
   dock tank drops as the 13.8 L cleaning event is drawn.
3. **Return + top-up** — the carriage climbs back and the tank refills over the
   next nights' harvest. The loop is closed.

### Labelled multi-view screenshots (correctly oriented)

| file | view |
|---|---|
| `figures/view_front_labeled.png` | **FRONT** — panel face-on, dock/tank in the foreground (you, standing on the ground in front of the panel) |
| `figures/view_side_labeled.png` | **SIDE** — the 24° tilt profile, dock at the low end |
| `figures/view_angled_labeled.png` | **ANGLED** front/side — panel face + side + dock |
| `figures/view_top_labeled.png` | **TOP** — footprint (dock, rails, panel, carriage) |

Every component is called out, including the **mounting frame** (tall back posts
+ short front legs + purlins) that carries the tilted panel. Action stills:
`figures/sim_fill_full.png`, `sim_washing.png`, `sim_clean_done.png`.

> **Honest note.** Gazebo Classic has no fluid solver, so the **tank fill is real
> geometry** (column height = the reservoir level the co-simulation computes)
> while the **spray is a visual cue**. The scene geometry is exactly what the
> integrated-world SDF (`worlds/awh_pvbot_integrated.sdf`) loads in Gazebo.

## What the integration shows (the analysis)

The robot needs water and the AWH makes water; until now those lived in separate
folders. This couples them through a shared **dock reservoir** and runs a daily,
year-long water+energy balance over real NASA POWER climate at six Egyptian
sites × three deployment scales. Residential headline (9.9 kWp, 46 m²):

| Site | Demand (L/yr) | Sized bed (kg) | Min kg (0 deficit) | Deferred cleans | TEC tiles | Parasitic (% array) |
|---|---|---|---|---|---|---|
| Benban (Aswan) | 1435 | 67.6 | **76.5** | 6 | 57 | 1.64 |
| Mansoura | 1435 | 44.5 | 42.0 | 0 | 38 | 1.32 |
| New Alamein | 1435 | 46.4 | 42.1 | 0 | 39 | 1.30 |
| Hurghada | 1435 | 58.0 | 60.9 | 2 | 49 | 1.43 |
| Siwa | 1435 | 52.0 | 58.2 | 5 | 44 | 1.35 |
| New Admin. Capital | 1435 | 44.6 | 45.5 | 1 | **38** | 1.23 |

1. **The loop closes everywhere** at residential scale with a 42–77 kg silica
   bed (fits the 0.4 m dock cube). The TEC-tile column lands on **38 tiles at
   NAC = the as-built dock** — a validation against the hardware.
2. **The constraint is the summer low-humidity spell, not the annual average.**
   Arid sites (Benban, Siwa) need *more* than the 20 % annual margin; humid Delta
   sites need less.
3. **Self-supply is scale-invariant** and the parasitic load is tiny: harvesting +
   cleaning draw **1.2–1.6 %** of the array's own output while recovering
   thousands of kWh/yr in avoided soiling loss.

Full write-up: **`AWH_PVBOT_INTEGRATION.pdf`** (6 pp).

## Folder map

```
AWH_PVBOT_DELIVERABLE/
├─ README.md                     ← you are here
├─ AWH_PVBOT_INTEGRATION.pdf/.tex← the analysis report
├─ code/
│  ├─ demo_render.py             ← the simulation video + labelled views (self-contained)
│  ├─ awh_pvbot_cosim.py         ← the coupled annual water+energy balance
│  ├─ make_figures.py            ← the six analysis figures
│  ├─ awh_water_bus.py           ← live ROS 2 coupling node (+ testable core)
│  ├─ test_water_bus.py          ← off-board year-long self-check
│  ├─ run_integrated_demo.sh     ← live Gazebo+ROS demo (run in WSL, see note)
│  ├─ build_demo.py              ← original SDF generator + render
│  ├─ make_integrated_world.py   ← parametric integrated-world SDF
│  └─ make_awh_dock_sdf.py       ← the AWH cube resized to the residential need
├─ data/                         ← input climate + design data (self-contained)
├─ results/                      ← co-sim outputs (CSV/JSON)
├─ figures/                      ← the sim video, GIF, labelled views, stills, analysis figures
├─ worlds/                       ← awh_pvbot_integrated.sdf, awh_dock_world.sdf
└─ docs/                         ← INTEGRATION_LOG.md, RENDER_DEMO.md
```

## Re-run

```bash
# the simulation video + labelled views (self-contained — runs from this folder)
python code/demo_render.py            # -> figures/awh_pvbot_sim.mp4 + .gif + view_*_labeled.png

# the analysis (reads ../awh_sim and ../output in the full project tree)
python code/awh_pvbot_cosim.py        # -> results/
python code/make_figures.py           # -> figures/
python code/test_water_bus.py         # WaterBus self-check (NAC: f=1.21)
```

> **Note.** `demo_render.py` is fully standalone (reads only `results/`). The
> analysis scripts and the live-Gazebo launcher read sibling project folders
> (`awh_sim/`, `output/`, `gazebo/`) and are meant to run from the original
> project tree; their **outputs are already included here** in `results/`,
> `figures/`, and `worlds/`. The live Gazebo demo needs WSL2 + ROS 2 Humble +
> Gazebo Classic 11.

## Honesty notes

- Gazebo Classic has no fluid: tank fill is real geometry, spray is a cue.
- The fill rate is the real per-night harvest from the climate data (NAC
  ~4.7 L/night, 45 kg bed); one night is not enough, so the dock fills over ~5
  fast-forwarded nights.
- Soiling is a single 1 %/day rate with a 3.5 % clean threshold — reproduces the
  design cadence, defensible for desert Egypt, but real soiling is episodic.
- Recovered-energy compares against a never-cleaned panel saturating at ~50 %
  loss, so it is an upper bound on the value of cleaning.
