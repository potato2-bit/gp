#!/usr/bin/env python3
"""Generate the RESIDENTIAL-sized AWH dock model, parameterised by tank water level.

This is the family nested-cube AWH resized to the residential robot's actual
need. The co-simulation (integration/awh_pvbot_cosim.py) sizes the silica bed at
~45 kg (humid-Delta / NAC) to ~68 kg (arid Benban). At a silica bulk density of
750 kg/m3 that is 0.060-0.090 m3 of gel, so a ~0.40 m gel cube (0.064 m3 ~ 48 kg)
covers the NAC/Delta case -- about HALF the linear size of the 1 m family cube.
The whole dock therefore drops onto the 0.40 x 0.70 m plinth footprint already in
panel_world_tilt.sdf at the bottom of the rail.

Emits EITHER a full standalone world (--world) for quick viewing, or a bare
<model> block (default) to be <include>-style pasted into the integrated world.

  python make_awh_dock_sdf.py --water 0.10 --world --out awh_dock_world.sdf
  python make_awh_dock_sdf.py --water 0.10 --out _dock_model.sdf      # model only
"""
from __future__ import annotations
import argparse

# --- residential dock geometry (metres) -------------------------------------
S = 0.5                       # global scale vs the 1 m family cube
GEL = 0.40                    # gel cube side (0.064 m3 ~ 48 kg silica @ 750 kg/m3)
ENC = 0.50                    # glass enclosure side
WALL_Z = 0.52                 # enclosure height
BASIN = 0.48                  # collection basin side
BASIN_H = 0.06                # basin depth
TANK_MAX = 0.20               # max modelled water column height in the basin


def vis(name, pose, geom, rgba, transparency=0.0, spec=None):
    r, g, b, a = rgba
    sp = f"<specular>{spec}</specular>" if spec else ""
    return (f'        <visual name="{name}"><pose>{pose}</pose>'
            f'<geometry>{geom}</geometry><transparency>{transparency}</transparency>'
            f'<material><ambient>{r} {g} {b} {a}</ambient>'
            f'<diffuse>{r} {g} {b} {a}</diffuse>{sp}</material></visual>\n')


def box(x, y, z):
    return f"<box><size>{x} {y} {z}</size></box>"


def cyl(r, l):
    return f"<cylinder><radius>{r}</radius><length>{l}</length></cylinder>"


def model(water_h, name="awh_dock"):
    """Bare <model> block for the residential AWH dock, water column = water_h."""
    p = []
    # plinth that mates the dock footprint in panel_world_tilt.sdf
    p.append(vis("plinth", "0 0 0.03 0 0 0", box(0.40, 0.70, 0.06), (0.30, 0.32, 0.36, 1)))
    # collection basin / tank
    p.append(vis("tank_basin", "0 0 0.09 0 0 0", box(BASIN, BASIN, BASIN_H), (0.10, 0.45, 0.55, 1)))
    # condensate water column (grows with --water) -- THIS is the fill animation
    wh = max(0.0, min(TANK_MAX, water_h))
    if wh > 0.001:
        zc = 0.12 + wh / 2.0
        p.append(vis("water", f"0 0 {zc:.4f} 0 0 0", box(BASIN - 0.04, BASIN - 0.04, wh),
                     (0.10, 0.55, 0.95, 1), transparency=0.20))
    # legs holding the gel cube above the basin
    for sx, sy, nm in ((0.13, 0.13, "lf"), (-0.13, 0.13, "lb"),
                       (0.13, -0.13, "rf"), (-0.13, -0.13, "rb")):
        p.append(vis(f"leg_{nm}", f"{sx} {sy} 0.20 0 0 0", box(0.025, 0.025, 0.16),
                     (0.2, 0.2, 0.22, 1)))
    # inner silica-gel adsorbent cube (~48 kg)
    p.append(vis("gel_cube", "0 0 0.40 0 0 0", box(GEL, GEL, GEL), (0.12, 0.40, 0.85, 1)))
    # outer transparent glass enclosure: 4 walls + top
    glass = (0.55, 0.70, 0.85, 1)
    half = ENC / 2
    p.append(vis("wall_front", f"0 {-half} 0.40 0 0 0", box(ENC, 0.02, WALL_Z), glass, 0.68, "0.4 0.5 0.6 1"))
    p.append(vis("wall_back",  f"0 {half} 0.40 0 0 0",  box(ENC, 0.02, WALL_Z), glass, 0.68, "0.4 0.5 0.6 1"))
    p.append(vis("wall_left",  f"{-half} 0 0.40 0 0 0", box(0.02, ENC, WALL_Z), glass, 0.68, "0.4 0.5 0.6 1"))
    p.append(vis("wall_right", f"{half} 0 0.40 0 0 0",  box(0.02, ENC, WALL_Z), glass, 0.68, "0.4 0.5 0.6 1"))
    p.append(vis("glass_top",  "0 0 0.66 0 0 0",        box(ENC, ENC, 0.02),    glass, 0.72, "0.4 0.5 0.6 1"))
    # stack chimney (night natural-convection vent) + cap
    p.append(vis("chimney", "0 0 0.80 0 0 0", cyl(0.04, 0.26), (0.30, 0.30, 0.33, 1)))
    p.append(vis("chimney_cap", "0 0 0.94 0 0 0", cyl(0.06, 0.02), (0.22, 0.22, 0.24, 1)))
    # base intake louvres
    for vx, vy, sx, sy, nm in ((0, -0.255, 0.18, 0.015, "f"), (0, 0.255, 0.18, 0.015, "b"),
                               (-0.255, 0, 0.015, 0.18, "l"), (0.255, 0, 0.015, 0.18, "r")):
        p.append(vis(f"vent_{nm}", f"{vx} {vy} 0.16 0 0 0", box(sx, sy, 0.06), (0.12, 0.12, 0.14, 1)))
    # delivery line cue back to the carriage tank (the water bus)
    p.append(vis("feed_line", "0.30 0 0.12 0 1.4 0", cyl(0.008, 0.50), (0.15, 0.55, 0.85, 1)))
    body = "".join(p)
    return (f'    <model name="{name}"><static>true</static>\n'
            f'      <pose>-1.05 0 0 0 0 0</pose>\n'
            f'      <link name="dock">\n{body}      </link>\n'
            f'    </model>\n')


def world(water_h):
    return f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="awh_dock_world">
    <light name="sun" type="directional"><pose>0 0 10 0 0 0</pose>
      <diffuse>0.95 0.95 0.92 1</diffuse><specular>0.25 0.25 0.25 1</specular>
      <direction>-0.4 0.3 -0.9</direction></light>
    <model name="ground"><static>true</static><link name="l">
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>50 50</size></plane></geometry>
        <material><ambient>0.72 0.72 0.74 1</ambient><diffuse>0.78 0.78 0.80 1</diffuse></material></visual>
    </link></model>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.86 0.91 0.97 1</background><shadows>true</shadows></scene>
{model(water_h)}  </world>
</sdf>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--water", type=float, default=0.10, help="water column height (m), 0..0.20")
    ap.add_argument("--world", action="store_true", help="emit a full standalone world")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    txt = world(a.water) if a.world else model(a.water)
    open(a.out, "w").write(txt)
    print(f"wrote {a.out}  (water_h={a.water}, world={a.world})")


if __name__ == "__main__":
    main()
