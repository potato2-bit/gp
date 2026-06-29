# AWH — Gazebo models (standalone AWH project)

Viewable 3D models of the solar-regenerated silica-gel atmospheric water harvester.
Two form factors:

## 1. Family-scale **nested cube** (box-in-box) — recommended for households
`awh_cube_world.sdf` — passive solar-desiccant design (the lab-experiment geometry):
| Part | Role | Colour |
|---|---|---|
| Outer transparent cube | glass solar enclosure (daytime regeneration) + condensing surface | clear |
| Inner cube | silica-gel adsorbent bed (on legs) | blue |
| Basin / tank | collects condensate that runs down the cool glass | teal |
| Water | rising condensate | light blue |
| Stack chimney | night natural-convection outlet (warm moist air out) | dark |
| Base louvres | night air intake (cool air in) — damped shut by day | dark |

Passive (no fan/collector hardware) → cheap, robust, repairable: the right trade for
families. The **stack chimney + base louvres** drive night airflow by buoyancy (cool air
in low, warm moist air out high). CADET shows that as long as this gives a face velocity
**≳ 0.02 m/s**, the passive bed reaches ~89–98 % of the forced-flow water (the bed
equilibrates over a 12 h night) — so the design keeps nearly the full yield with no fan.
By day the louvres close so the box traps solar heat and condenses on the cool glass.

**View / render:**
```bash
gazebo gazebo/awh_description/awh_cube_world.sdf      # interactive
bash  gazebo/awh_description/animate_fill.sh          # frames + GIF + labeled shot
```
Outputs: `awh_cube_labeled.png` (labeled components), `awh_fill.gif` (tank-filling
animation), `awh_fill_empty.png` / `awh_fill_full.png`, frame PNGs in `frames/`.
`make_cube_sdf.py --water H --camera --out f.sdf` regenerates a world at any tank level.

## 2. Industrial unit (1 m³ packed bed + fan + collector)
`awh_world.sdf` / `awh_shot.png` — the forced-flow embodiment used for the 1 m³
utility-scale calculations (cylindrical bed, tilted collector, condenser, fan).
`bash make_shot.sh` renders it.

## Notes
- Animation is a GIF (PIL); install `ffmpeg` if you want an MP4 instead.
- Headless rendering uses a camera sensor + `<save>` via `gzserver` with `DISPLAY=:0`
  (WSLg). Frames are written under `/tmp` then copied out within one run.
