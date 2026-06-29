# Component map — Gazebo model vs. the designed robot

This is the proof that `pvbot_railed_control.urdf` (carriage) and the
`awg_dock` model in `panel_world_tilt.sdf` (dock) match the finalized
rail-guided TEC PV-cleaning robot. Every major real part is a distinct URDF/SDF
element with its budget mass, its datasheet or CAD dimensions, and its place on
the machine.

Mass target: **8.00 kg** carriage (Option B, TEC docked, 10 Ah battery). The
model sums to **7.991 kg** — delta −0.009 kg, inside ±3 %.

Sources keyed below:
`EL` = `ELECTRICAL_DESIGN.tex` (Table `tab:weight`, committed-parts table);
`CAD` = `CAD_DESIGN_PACKAGE.tex` + drawing register D-101…D-110;
`BOM` = `MARKET_PARTS_BUYLIST.md` / `MINIMUM_PROTOTYPE_BUYLIST.md`;
`JSON` = `output/rail_guided_design.json`.

## Carriage (links in `pvbot_railed_control.urdf`)

| Real component | Source | Mass (kg) | Dimensions | URDF link | Where |
|---|---|---|---|---|---|
| Chassis base plate, Al 6061-T6 3 mm | CAD D-101; EL tab:weight | 1.100 | 0.30 × 0.92 × 0.10 m (gantry envelope) | `base_link` | carriage |
| Carriage side-frame (left) | CAD D-108; EL (2× = 0.80) | 0.400 | 0.34 × 0.02 × 0.12 m | `side_frame_left` | carriage |
| Carriage side-frame (right) | CAD D-108; EL (2× = 0.80) | 0.400 | 0.34 × 0.02 × 0.12 m | `side_frame_right` | carriage |
| Full-width brush 0.96 m, Ø50 core | CAD D-103/D-110; JSON; EL | 1.000 | r = 0.040 m, L = 0.96 m | `brush_link` | carriage |
| Brush motor GA25-370 (100 rpm) | EL; BOM §3 | 0.105 | Ø24.4 × 62 mm | `brush_motor` | carriage |
| Drive motor GA25-370 1:71 (left) | EL; BOM §1 (2× = 0.21) | 0.105 | Ø24.4 × 62 mm | `drive_motor_left` | carriage |
| Drive motor GA25-370 1:71 (right) | EL; BOM §1 (2× = 0.21) | 0.105 | Ø24.4 × 62 mm | `drive_motor_right` | carriage |
| Steel pinion Ø30 M1 (left, meshes +y rack) | JSON; EL; BOM §1 (2× = 0.06) | 0.030 | Ø30 × 12 mm | `pinion_left` | carriage |
| Steel pinion Ø30 M1 (right, meshes −y rack) | JSON; EL; BOM §1 (2× = 0.06) | 0.030 | Ø30 × 12 mm | `pinion_right` | carriage |
| Motor driver MDD3A + 2× IRLZ44N MOSFET | EL; CAD D-106; BOM §1,§3 | 0.050 | 45 × 45 × 22 mm box | `driver_box` | carriage |
| Water pump, 12 V diaphragm | CAD D-105; EL; BOM §4 | 0.300 | 90 × 40 × 35 mm | `water_pump` | carriage |
| Water tank 3.6 L (HDPE) + spray bar + nozzles, **plus 1.8 L mean water fill** | CAD D-105; EL (0.40 dry + 1.80 water) | 2.200 | 166 × 226 × 96 mm internal | `tank_link` | carriage |
| Spray bar 0.96 m + 9 flat-fan nozzles | CAD D-103; BOM §4 (mass in tank-dry line) | 0.001 | r = 0.012 m, L = 0.92 m + 9 nozzle cones | `spray_bar` | carriage |
| Battery 12 V 10 Ah LFP, 15 A BMS | EL; BOM §6 | 1.300 | 150 × 100 × 95 mm | `battery` | carriage |
| ESP32 DevKit (real-time MCU) | EL; BOM §7 | 0.010 | 58 × 28 × 13 mm | `esp32` | carriage |
| Raspberry Pi 4B + heatsink (ROS 2 host) | EL; BOM §7 | 0.055 | 85 × 56 × 20 mm | `rpi4` | carriage |
| Sensor cluster: DHT22, 2× DS18B20, INA219, MPU-6050, 2 limit switches | EL; BOM §5 | 0.100 | 60 × 40 × 20 mm box + 2 switch nubs | `sensor_cluster` | carriage |
| Cabling, connectors, fuses | EL; BOM §6 | 0.300 | 0.20 × 0.30 × 0.010 m tray | `wiring_tray` | carriage |
| V-groove guide bogie + 2 wheels (front-right) | CAD D-108; EL (8 wheels / 4 bogies = 0.40) | 0.100 | 60 × 30 × 50 mm + 2× Ø24 wheels | `bogie_fr` | carriage |
| V-groove guide bogie + 2 wheels (rear-right) | CAD D-108; EL | 0.100 | 60 × 30 × 50 mm + 2× Ø24 wheels | `bogie_rr` | carriage |
| V-groove guide bogie + 2 wheels (front-left) | CAD D-108; EL | 0.100 | 60 × 30 × 50 mm + 2× Ø24 wheels | `bogie_fl` | carriage |
| V-groove guide bogie + 2 wheels (rear-left) | CAD D-108; EL | 0.100 | 60 × 30 × 50 mm + 2× Ø24 wheels | `bogie_rl` | carriage |
| **Carriage total (excl. `world`, `rail_base`)** | | **7.991** | envelope ≈ 0.30 × 0.92 × 0.20 m | 22 links | — |

Two budget lines are folded so the model does not double-count:

- The "tank dry + spray bar + nozzles + tube = 0.40 kg" line and the
  "water mean fill = 1.80 kg" line both sit on `tank_link` (2.20 kg), with the
  `spray_bar` link carrying a 0.001 kg token so its geometry shows without
  adding mass.
- V-groove wheels and bogie plates (0.40 kg, 8 wheels) are split across the four
  `bogie_*` links at 0.10 kg each.

Inertias for every resized link come from `scripts_inertia_helper.py` (solid
box `I = m/12·(a²+b²)`, solid cylinder `I_axis = ½mr²`,
`I_trans = m(3r²+L²)/12`).

## Dock — TEC atmospheric-water-generation module (`awg_dock` in `panel_world_tilt.sdf`)

The finalized residential design takes the thermoelectric condenser **off the
carriage**. Keeping it on, alongside an honest 10 Ah pack, was fine; alongside a
real 20 Ah pack it would push the carriage near 11 kg. The fix in
`ELECTRICAL_DESIGN.tex` is to dock the TEC (its 1.05 kg leaves the carriage) and
top up water and charge at the dock between cleans. The dock is **static** and
sits at the bottom of the rail (world x ≈ −1.05).

| Dock element | Source | Geometry | SDF visual |
|---|---|---|---|
| Enclosure plinth | CAD D-104 layout | 0.40 × 0.70 × 0.12 m | `plinth` |
| Al cold plate | CAD D-104 (170 mm plate) | 0.20 × 0.40 × 0.006 m | `cold_plate` |
| TEC tile array (representative 2×4 = 8 of TEC1-12706) | BOM §5; EL (4 bench / 38 NAC) | 8× 40 × 40 × 4 mm at 85 mm pitch | `tile_00`…`tile_13` |
| Hot-side finned heat sinks (4×) | CAD D-104 (80 × 80 × 25 mm) | 4× 80 × 80 × 25 mm + fin band | `sink_0`…`sink_3`, `fins_a` |
| Cooling fans (2×, 120 mm) | BOM §5 | 2× Ø120 × 25 mm | `fan_l`, `fan_r` |
| Condensate collection tank | CAD D-104 drain; water-harvesting | 0.14 × 0.22 × 0.16 m + Ø6 drain tube | `cond_tank`, `drain` |
| Power box: EPever MPPT + dock LFP bank + 48 V string switches (IRLB4030 ×10) | EL (dock 48 V bus); BOM §6,§5 | 0.16 × 0.24 × 0.18 m + MPPT face | `power_box`, `mppt_face` |
| PV-tie panel cue (dock runs off PV via MPPT) | EL (PV → MPPT → bank) | 0.30 × 0.22 × 0.012 m | `pv_tie` |

The tile grid is representative. The bench prototype runs a 2×2 = 4-tile cold
plate; the residential NAC dock scales the same array to 38 tiles wired as nine
series-quads plus one pair, each string on its own IRLB4030 100 V switch.

## Validation log (this build)

- `check_urdf pvbot_railed_control.urdf` — parses; lists `base_link` + 21
  child links; `world` → `rail_base` → `base_link` chain intact.
- Mass sum over all links except `world`/`rail_base` = **7.991 kg** (target
  8.00, delta −0.009, inside ±3 %).
- Drive test (`test_launch.sh`, headless): `joint_state_broadcaster` and
  `rail_velocity_controller` both **Configured and activated**; the sweep node
  drives `rail_slide` down then up over a **1.006 m** range at **≈0.088 m/s**
  (0.176 m per 2 s sample), matching the pre-change baseline (range 1.005 m).
  No load errors from the world (AWG dock loads clean).

## What stayed protected (unchanged)

`world` link, `rail_base` link, `world_fix` fixed joint, `rail_slide` prismatic
joint (effort = 45 N, the rack-and-pinion DOF), the `<ros2_control>` block, the
`libgazebo_ros2_control` plugin and its `controllers.yaml` path, and the
`<gazebo reference=...>` colour tags. The file still opens with a comment (no
`<?xml?>` declaration), which `gazebo_ros2_control`'s param parser needs.

## Remaining gaps (model vs. real design)

- The pinions are visual cylinders fixed to `base_link`; the rack-and-pinion
  mesh is modelled as the single `rail_slide` prismatic DOF with the motor
  effort ceiling (45 N), not as a rotating gear pair. This is deliberate — it is
  the validated, smooth drive — but the pinion teeth do not physically roll on
  the rack.
- The brush and spray are static visuals (no spinning roller joint, no fluid).
  The brush motor and pump are present as mass and geometry only.
- The dock TEC tile array is shown as a representative 8-tile grid, not the full
  38-tile NAC bank, to keep the scene readable.
- `tank_link` carries the mean water fill (1.8 L) as fixed mass; it does not
  drain during a sweep, so the as-modelled mass is the mean-fill case, not the
  full-to-empty range.
