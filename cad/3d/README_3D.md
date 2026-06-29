# 3D CAD model — rail-guided TEC PV-cleaning robot

REE598 graduation project. Date 2026-06-13. Units: millimetres.

This folder holds the 3D model of the rail-guided carriage robot and the
panel/rail scene it runs on. The primary deliverable is a set of AutoCAD
script files (`.scr`) that build native 3D ACIS solids. A faceted-mesh
`.dxf` is provided as a viewer-friendly secondary copy.

Geometry basis: `output/rail_guided_design.json` (8.0 kg carriage, full-width
0.96 m brush at Ø50, Ø30 pinion, rack-and-pinion drive, two 2.4 m rails) and
`gazebo/pvbot_description/pvbot.urdf` (link sizes and the TEC stack, tank, and
spray-bar layout). Link names and sizes match the URDF.

## Files

| File | What it builds |
|---|---|
| `pvbot_3d_assembly.scr` | The carriage robot: chassis plate, TEC AWG module (cold plate + 4 tiles + finned hot sink + 2 fans), 3.6 L tank, full-width 0.96 m brush roller, spray bar + 9 nozzles, carriage side-frames with V-groove wheels, rack-and-pinion drive. |
| `rail_and_panel_3d.scr` | The fixed scene: 2.0 × 1.0 m PV panel at 24° on four posts, twin 2.4 m V-slot rails, rack strips (4.8 m total), end stops. |
| `scene_3d.scr` | Nests the two scripts above so the carriage sits on the rails in one drawing. |
| `pvbot_3d.dxf` | The same geometry as faceted 3D `MESH` entities (59 meshes), for any DXF viewer. Audited clean (0 errors). |
| `make_pvbot_3d_dxf.py` | Generator for the DXF (single dimension source). Run `python cad/3d/make_pvbot_3d_dxf.py`. |

## Coordinate frame

Same as the URDF: **+X** down the fall-line (direction of travel), **+Y** along
the brush axis across the 0.96 m width, **+Z** up out of the glass. Deck top is
z = 0; the glass plane (brush contact) is at z = −50. Both `.scr` files are
drawn flat in this frame, so the robot script overlays the rail script directly.
A commented `ROTATE3D` block at the end of `rail_and_panel_3d.scr` tilts the
finished scene 24° onto its posts if you want the as-installed pose.

## How to open in AutoCAD 2026

1. Start a new drawing from the metric template `acadiso.dwt` (millimetres).
2. Type `SCRIPT`, press Enter, and pick the `.scr` file
   (for the whole scene pick `scene_3d.scr`; keep all three `.scr` files in the
   same folder so the nested calls resolve).
3. The script sets its own layers, builds the solids, and ends with `ZOOM E`.
4. If the view does not frame automatically, type `ZOOM` then `E` (extents).
5. For the isometric: type `-VIEW` then `SWISO` (south-west isometric).
6. For shaded display: type `VSCURRENT` then `R` (Realistic). Use `2` (2D
   wireframe) to go back to lines.

If your security settings block nested `SCRIPT` calls inside `scene_3d.scr`,
run the two component scripts by hand instead: `rail_and_panel_3d.scr` first,
then `pvbot_3d_assembly.scr`. The result is identical.

To open the DXF instead: `OPEN` → `pvbot_3d.dxf`, then `SWISO` and `VSCURRENT`
→ Realistic as above. The DXF also opens in LibreCAD, QCAD, FreeCAD, and DWG
TrueView.

## Layers

Each subsystem is on its own named layer with a distinct colour, so you can
isolate it with `LAYISO` or toggle it in the Layer Properties manager:
`CHASSIS`, `FRAME`, `TEC_COLD`, `TEC_TILE`, `TEC_SINK`, `TEC_FAN`, `TANK`,
`BRUSH`, `SPRAY`, `NOZZLE`, `DRIVE`, `WHEEL` (robot) and `GLASS`, `PFRAME`,
`POST`, `RAIL`, `RACK`, `STOP` (scene), plus `TEXT`.

## Invented (workshop) dimensions

The frozen JSON fixes the masses, the brush length and diameter, the pinion
diameter, the rail and rack lengths, the panel size, and the tilt. The values
below are workshop choices made to draw a buildable model; revise them without
touching the analysis.

| Item | Value used | Why |
|---|---|---|
| Chassis plate | 400 × 300 × 10 mm | URDF base_link footprint; 10 mm as a structural carriage plate |
| TEC stack heights (cold plate, tiles, sink, fins, fans) | per URDF tec_module, deck-relative | copied from `pvbot.urdf` with the 60 mm joint offset removed |
| Carriage side-frame arms | 20 mm plate, ribs 30 mm, reach to y = ±510 | bridge the deck edge (±150) out to the rails just outside the brush |
| V-groove wheel | Ø24 × 16 mm, 4 per side | OpenBuilds mini V-wheel class (see `MARKET_PARTS_BUYLIST.md`) |
| Drive-motor body | Ø28 × 78 mm | GA25-370 gearmotor envelope (buy-list §1) |
| Pinion hub | Ø30 × 12 mm | module-1 z30 pinion, Ø30 from the JSON |
| Rail section | 20 × 40 mm (2040 V-slot) with shallow V-ribs | OpenBuilds 2040 extrusion; ribs approximate the wheel seat without booleans |
| Rack strip | 12 × 8 mm band on the rail inner face | module-1 steel rack |
| Panel frame / posts | 35 mm frame, 50 × 50 mm legs | typical residential module frame and a light post stand |
| Nozzle cones | Ø18 × 18 mm, 100 mm pitch | nine flat-fan nozzles across the 0.96 m bar |

The brush is drawn as a Ø80 bristle shell over a Ø50 core; the JSON Ø50 is the
roller core diameter and matches the URDF `brush_link` cylinder (r = 0.04 m
visual). The cold-plate face and tank wall thicknesses follow the URDF box
sizes directly.
