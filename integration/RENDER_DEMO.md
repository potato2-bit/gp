# Integrated AWH <-> PVbot demo — how to produce the screenshots + video

Everything is built and bug-checked; it just needs to be **run** (this worker
fork's shell was permission-gated, so the image/video files were not written).

## One command (Windows, no WSL, no Gazebo needed)

```bash
python integration/build_demo.py
```

Produces, under `integration/figures/`:

| artifact | what it shows |
|---|---|
| `shot_fill_empty.png` | AWH dock, tank empty, carriage parked at top |
| `shot_fill_full.png` | AWH dock tank **filled** (real water-column height) |
| `shot_mid_clean.png` | carriage mid-sweep, spray on, panel half dirty/half clean |
| `shot_clean_done.png` | panel fully cleaned |
| `awh_pvbot_demo.gif` | full loop: **tank filling -> cleaning sweep (spray) -> return + top-up** |
| `awh_pvbot_demo.mp4` | same, if `ffmpeg` is on PATH (else GIF only) |
| `frames/frame_###.png` | all 66 frames |

It also (re)writes the two SDF worlds:
`gazebo/awh_description/awh_dock_world.sdf` and
`integration/awh_pvbot_integrated.sdf`.

## What was resized / created

- **`gazebo/awh_description/make_awh_dock_sdf.py`** — the family nested-cube AWH
  **resized to the residential robot's actual need**: a ~0.40 m silica cube
  (0.064 m3 ~ **48 kg gel**, matching the co-sim's 44.6 kg NAC / 67.6 kg Benban
  sizing), ~0.5x the linear size of the 1 m family cube, dropped onto the
  0.40 x 0.70 m dock plinth at the rail base. Tank water level is a parameter,
  so the same model drives the fill animation.
- **`integration/make_integrated_world.py`** — one Gazebo world holding the
  24 deg panel + guide rails + the cleaning carriage + the resized AWH dock,
  parameterised by carriage position, tank level, spray on/off, and cleaned
  fraction.
- **`integration/build_demo.py`** — headless 3D renderer (matplotlib, same
  geometry the SDF loads) that animates the integration story.

## Honest scope note

Gazebo Classic has **no native fluid/particle simulation** (per
`gazebo/pvbot_description/COMPONENT_MAP.md`: spray and brush are static visuals,
"no spinning roller joint, no fluid"). So in the render:
- the **tank fill is physical** — the water-column height is the real reservoir
  level the co-sim computes;
- the **wash is a cue** — a translucent spray sheet under the brush plus the
  panel transitioning dirty->clean as the carriage sweeps. That is the faithful
  way to show "water washing" in this engine.

## Optional: the same scene live in Gazebo (WSL)

When WSL/Gazebo is up, the generated world loads directly:

```bash
gazebo gazebo/awh_description/awh_dock_world.sdf        # resized dock alone
gazebo integration/awh_pvbot_integrated.sdf             # full integrated scene
```

For a Gazebo-rendered fill animation, reuse the existing camera-sensor path in
`gazebo/awh_description/animate_fill.sh` against the resized dock (it already
sweeps `make_*_sdf.py --water` across levels and stitches a GIF via PIL).
