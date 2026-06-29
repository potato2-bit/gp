#!/usr/bin/env python3
"""make_integrated_world.py -- the AWH <-> PVbot integrated Gazebo world.

Composes one scene from the two halves of the project:
  * the 24 deg tilted PV panel + the two guide rails + rack (panel_world_tilt.sdf)
  * the rail-guided cleaning carriage (simplified gantry box + brush + spray bar)
  * the RESIDENTIAL-sized AWH dock (gazebo/awh_description/make_awh_dock_sdf.py)

Parameterised so one generator drives both a static view and every animation
frame:
  --carriage  s in [0,1]   carriage position along the rail (1=top, 0=bottom dock)
  --water     h in [0,0.2] AWH dock tank water column (m)  -> the FILL animation
  --spray     0/1          spray cue + brush active on the current stroke
  --clean     f in [0,1]   fraction of the panel already cleaned (dirty->clean)

  python make_integrated_world.py --carriage 0.5 --water 0.1 --spray 1 \
         --clean 0.5 --out awh_pvbot_integrated.sdf
"""
from __future__ import annotations
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "gazebo", "awh_description"))
import make_awh_dock_sdf as dock  # noqa: E402

TILT = math.radians(24.0)
PANEL_L, PANEL_W = 2.0, 1.0
# panel surface plane: centre at z=0.50, pitched -24 deg about y (panel_world_tilt.sdf)
PZ0 = 0.50


def panel_point(u):
    """World (x,z) of a point a fraction u along the up-slope axis (u=1 top)."""
    s = (u - 0.5) * PANEL_L            # local x, -1..+1
    x = s * math.cos(TILT)
    z = PZ0 + s * math.sin(TILT)
    return x, z


def vis(name, pose, geom, rgba, transparency=0.0, spec=None):
    r, g, b, a = rgba
    sp = f"<specular>{spec}</specular>" if spec else ""
    return (f'      <visual name="{name}"><pose>{pose}</pose>'
            f'<geometry>{geom}</geometry><transparency>{transparency}</transparency>'
            f'<material><ambient>{r} {g} {b} {a}</ambient>'
            f'<diffuse>{r} {g} {b} {a}</diffuse>{sp}</material></visual>\n')


def box(x, y, z):
    return f"<box><size>{x} {y} {z}</size></box>"


def panel_model(clean_frac):
    """Panel split into a cleaned (dark blue, glossy) lower strip and a soiled
    (dusty tan) upper strip; the boundary is the brush front at clean_frac."""
    soiled = (0.62, 0.55, 0.40, 1)     # dust tan
    clean = (0.06, 0.10, 0.28, 1)      # clean PV blue
    parts = []
    # clean strip from bottom (u=0) up to clean_frac
    if clean_frac > 0.01:
        uc = clean_frac / 2.0
        xc, zc = panel_point(uc)
        Lc = clean_frac * PANEL_L
        parts.append(vis("glass_clean", f"{xc:.4f} 0 {zc:.4f} 0 {-TILT:.5f} 0",
                         box(Lc, PANEL_W, 0.02), clean, spec="0.6 0.6 0.7 1"))
    # soiled strip above
    if clean_frac < 0.99:
        us = (1 + clean_frac) / 2.0
        xs, zs = panel_point(us)
        Ls = (1 - clean_frac) * PANEL_L
        parts.append(vis("glass_soiled", f"{xs:.4f} 0 {zs:.4f} 0 {-TILT:.5f} 0",
                         box(Ls, PANEL_W, 0.02), soiled))
    # two guide rails along the slope
    for sgn, nm in ((1, "yp"), (-1, "yn")):
        cx, cz = panel_point(0.5)
        parts.append(vis(f"rail_{nm}", f"{cx:.4f} {0.51*sgn} {cz+0.045:.4f} 0 {-TILT:.5f} 0",
                         box(2.04, 0.04, 0.09), (0.25, 0.27, 0.30, 1)))
    return ('    <model name="pv_panel"><static>true</static>\n'
            '      <link name="glass">\n' + "".join(parts) + '      </link>\n    </model>\n')


def frame_model():
    """The ground-mount that carries the tilted panel: tall back posts + short
    front legs + top/low cross beams + under-panel purlins. Without it the panel
    would float (mirrors panel_frame in panel_world_tilt.sdf)."""
    col = (0.34, 0.36, 0.41, 1)
    xh, zh = panel_point(0.95)         # underside, high end
    xl, zl = panel_point(0.05)         # underside, low end
    cx, cz = panel_point(0.5)
    parts = []
    for sgn in (1, -1):
        sy = 0.46 * sgn
        parts.append(vis(f"post_h_{'p' if sgn>0 else 'n'}",
                         f"{xh:.4f} {sy} {zh/2:.4f} 0 0 0", box(0.06, 0.06, zh), col))
        parts.append(vis(f"leg_l_{'p' if sgn>0 else 'n'}",
                         f"{xl:.4f} {sy} {zl/2:.4f} 0 0 0", box(0.06, 0.06, zl), col))
        parts.append(vis(f"purlin_{'p' if sgn>0 else 'n'}",
                         f"{cx:.4f} {sy} {cz-0.055:.4f} 0 {-TILT:.5f} 0",
                         box(1.85, 0.04, 0.05), col))
    parts.append(vis("beam_top", f"{xh:.4f} 0 {zh+0.02:.4f} 0 0 0", box(0.06, 1.0, 0.05), col))
    parts.append(vis("beam_low", f"{xl:.4f} 0 {zl:.4f} 0 0 0", box(0.06, 1.0, 0.04), col))
    return ('    <model name="panel_frame"><static>true</static>\n'
            '      <link name="frame">\n' + "".join(parts) + '      </link>\n    </model>\n')


def carriage_model(s, spray):
    """Gantry carriage at rail fraction s (1=top). Brush + spray bar on the
    front (down-slope) edge; spray cue cone toggled by `spray`."""
    u = 0.20 + 0.62 * s                # keep it on the glass, not past the ends
    x, z = panel_point(u)
    nz = z + 0.10                       # ride height above the glass
    parts = []
    parts.append(vis("chassis", f"{x:.4f} 0 {nz:.4f} 0 {-TILT:.5f} 0",
                     box(0.30, 0.92, 0.12), (0.85, 0.86, 0.88, 1), spec="0.5 0.5 0.6 1"))
    parts.append(vis("tec_tank", f"{x:.4f} 0 {nz+0.08:.4f} 0 {-TILT:.5f} 0",
                     box(0.18, 0.40, 0.10), (0.20, 0.45, 0.75, 1)))
    # full-width brush + spray bar on the down-slope front edge
    xf, zf = panel_point(u - 0.09)
    parts.append(vis("brush", f"{xf:.4f} 0 {zf+0.05:.4f} {math.pi/2:.5f} 0 0",
                     "<cylinder><radius>0.04</radius><length>0.90</length></cylinder>",
                     (0.95, 0.85, 0.30, 1)))
    parts.append(vis("spray_bar", f"{xf:.4f} 0 {zf+0.085:.4f} {math.pi/2:.5f} 0 0",
                     "<cylinder><radius>0.012</radius><length>0.90</length></cylinder>",
                     (0.70, 0.72, 0.75, 1)))
    if spray:
        # translucent fan of water under the spray bar (Gazebo has no fluid; this
        # is the spray CUE -- a thin sheet hugging the glass just below the brush)
        xsp, zsp = panel_point(u - 0.13)
        parts.append(vis("spray_sheet", f"{xsp:.4f} 0 {zsp+0.02:.4f} 0 {-TILT:.5f} 0",
                         box(0.10, 0.88, 0.005), (0.30, 0.65, 0.95, 1), transparency=0.55))
    return ('    <model name="carriage"><static>true</static>\n'
            '      <link name="body">\n' + "".join(parts) + '      </link>\n    </model>\n')


def build(carriage, water, spray, clean):
    head = """<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="awh_pvbot_integrated">
    <light name="sun" type="directional"><pose>0 0 10 0 0 0</pose>
      <diffuse>0.95 0.95 0.92 1</diffuse><specular>0.3 0.3 0.3 1</specular>
      <direction>-0.4 0.3 -0.9</direction></light>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.86 0.91 0.97 1</background><shadows>true</shadows></scene>
    <model name="ground_plane"><static>true</static><link name="l">
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>60 60</size></plane></geometry>
        <material><ambient>0.70 0.70 0.72 1</ambient><diffuse>0.76 0.76 0.78 1</diffuse></material></visual>
    </link></model>
"""
    body = (panel_model(clean) + frame_model()
            + carriage_model(carriage, spray) + dock.model(water))
    return head + body + "  </world>\n</sdf>\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--carriage", type=float, default=0.7)
    ap.add_argument("--water", type=float, default=0.10)
    ap.add_argument("--spray", type=int, default=0)
    ap.add_argument("--clean", type=float, default=0.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    open(a.out, "w").write(build(a.carriage, a.water, a.spray, a.clean))
    print(f"wrote {a.out}  carriage={a.carriage} water={a.water} "
          f"spray={a.spray} clean={a.clean}")


if __name__ == "__main__":
    main()
