# pvbot_description — Gazebo model + cleaning demo

Rail-guided TEC PV-cleaning robot (REE598). **Gazebo Classic 11 + ROS 2 Humble**
under WSL2 (Ubuntu 22.04, WSLg). The carriage is a rail-guided gantry that rides
a rack-and-pinion up and down a **24° tilted panel**, cleaning with a full-width
brush + spray bar. The thermoelectric water condenser sits at a stationary
**dock** at the bottom of the rail (the residential design docks it to keep the
carriage under 8 kg).

## Run the demo — the real motor drive (recommended)

```bash
# the project is mounted in WSL at /mnt/c/...
cd "/mnt/c/Users/rizk/Desktop/GRADUATION PROJECT/gazebo/pvbot_description"
bash run_demo_motor.sh
```

This launches the **`gazebo_ros2_control`** stack: the carriage is constrained
to the rail by a prismatic joint and driven by an **effort-limited velocity
controller** whose force ceiling is the real motor (**45 N** = two GA25-370 1:71
through Ø30 mm pinions, `scripts/rack_pinion_drive.py`). It climbs because 45 N >
35.5 N load, and the motion is smooth because the joint is a hard constraint and
the loop is in the controller. Validated: a clean down-and-up sweep, ~1.0 m of
rail at ~0.09 m/s (the motor's real rail speed). Needs
`ros-humble-gazebo-ros2-control`.

The model is **component-accurate**: 22 carriage links, one per real part, summing
to 7.991 kg against the 8.00 kg budget — see `COMPONENT_MAP.md`.

## Alternative: the smooth kinematic glide

```bash
bash run_demo.sh
```

Spawns the simpler `pvbot.urdf` and glides it down/up the rail kinematically at
the motor's rail speed (no ros2_control needed). The clean visual if you don't
want to install controllers.

## Why rail-guided fall-line sweeps (the key design point)

A free differential-drive robot **cannot turn on a 24° glass face** in
simulation. It climbs and descends the fall line reliably, but any attempt to
yaw — in place or in an arc — stalls, because gravity overwhelms the
differential yaw authority and the wheels slip. Tested and confirmed: straight
fall-line motion holds dead-straight (y drift < 1 mm over a full pass), but
boustrophedon turns leave the robot stuck in one lane.

This is exactly why real rooftop PV cleaners (Ecoppia and similar) are
**rail-guided with a full-width brush**: a gantry carriage rides two rails along
the slope, the brush spans the whole panel width, and one straight sweep cleans
everything — no turning. The model follows that form:

- `panel_world_tilt.sdf` — 24° panel with **two prominent guide rails** running
  up the slope (the gantry rides between them), a **rack strip** along the +y
  rail for the rack-and-pinion drive, and **end stops** at the top and bottom.
- `pvbot.urdf` — the carriage is a **gantry**: a 0.92 m cross-beam spanning the
  panel on two wide driven wheels (track 0.90 m) plus a centre caster (a stable
  3-point stance), with the **0.90 m full-width brush + spray bar** hanging from
  its front edge between the rails.
- `pvbot_coverage.py` `mode:=sweep` — the gantry descends the rails on a
  gravity-assisted cleaning pass (spray + brush on), dead-straight.

Verified on the tilt: spawn near the top (z≈0.88), sweep down to the bottom
(z≈0.28), **y held to a few mm**, riding between the rails the whole way.

**On the return:** the real drive is a **rack-and-pinion** — a positive, geared
drive that cannot slip. A free-wheel friction model cannot climb 24° glass (the
wheels break traction and slide), so `run_demo.sh` cleans on the down-sweep and
then resets the carriage to the top to represent the geared return stroke. The
descent is the cleaning pass; the rack-and-pinion handles the powered return.

## Files

| file | what it is |
|------|------------|
| `pvbot.urdf` | **authoritative model** — spawn THIS. Chassis + TEC module + tank + full-width brush + spray bar + diff drive. 6.00 kg. |
| `panel_world_tilt.sdf` | **demo world** — 24° panel, guide rails, grippy glass |
| `panel_world_flat.sdf` | flat panel-on-frame — optional sanity run (`mode:=boustro`) |
| `panel_world.sdf` | bare 24° panel (no rails) — static view only |
| `pvbot_coverage.py` | coverage driver: `mode:=sweep` (tilt, default) or `mode:=boustro` (flat) |
| `run_demo.sh` | brings the whole tilted demo up |
| `validate_tilt_cov.sh` | headless self-test of the rail-guided sweep |
| `pvbot.urdf.xacro` | minimal inertia skeleton, not used by the demo |

## If you don't see the TEC / tank / spray

You are spawning an old `pvbot.urdf`. Confirm the current model:

```bash
source /opt/ros/humble/setup.bash
check_urdf pvbot.urdf                          # 8 children incl. tec_module, tank_link, spray_bar
gz sdf -p pvbot.urdf | grep -c tec_module_visual   # expect 14
```

In Gazebo Classic the TEC, tank, spray and caster are fixed to the chassis, so
they appear lumped under `base_link` — they still render.

## Manual bring-up (separate terminals)

```bash
source /opt/ros/humble/setup.bash
cd .../gazebo/pvbot_description

# terminal 1 — tilted world with the ROS factory
gazebo --verbose panel_world_tilt.sdf \
  -s libgazebo_ros_init.so -s libgazebo_ros_factory.so

# terminal 2 — spawn near the top of the slope, pitched to the glass
ros2 run gazebo_ros spawn_entity.py -entity pvbot -file pvbot.urdf \
  -x 0.65 -y 0 -z 0.91 -P -0.41888

# terminal 3 — rail-guided cleaning sweep
python3 pvbot_coverage.py --ros-args \
  -p mode:=sweep -p clean_speed:=0.06 -p stroke_len:=1.4 -p n_sweeps:=2
```

## Headless check (no GUI)

```bash
bash validate_tilt_cov.sh
# spawns on the 24 deg panel, runs the sweep, prints odom descending then
# climbing with y held near zero - confirms it stays on the panel.
```

## Notes

- Wheel μ = 0.9, panel μ = 0.9, small caster μ = 0.45 — grip without scrubbing.
- Spray and brush lift on any non-cleaning segment so nothing drags dry.
- Flat-panel boustrophedon still works for a level surface:
  `python3 pvbot_coverage.py --ros-args -p mode:=boustro` with
  `panel_world_flat.sdf`.
- Sweep parameters: `clean_speed`, `stroke_len`, `n_sweeps` — all `-p`
  overridable. True design cleaning speed is 0.05 m/s.
