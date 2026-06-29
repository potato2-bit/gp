#!/usr/bin/env python3
"""Generate the nested-cube (box-in-box) AWH SDF world, parameterised by tank water level.

Family-scale passive solar-desiccant design:
  - OUTER transparent cube  : glass solar enclosure + condensing surface
  - INNER cube              : silica-gel adsorbent bed (on legs)
  - BASIN/TANK at the floor : collects condensate (water box grows with --water)
Used both for interactive viewing and for rendering the tank-filling animation frames.
"""
from __future__ import annotations
import argparse


def vis(name, pose, geom, rgba, transparency=0.0, spec=None):
    r, g, b, a = rgba
    s = f"""      <link name="{name}">
        <pose>{pose}</pose>
        <visual name="v">
          <geometry>{geom}</geometry>
          <transparency>{transparency}</transparency>
          <material>
            <ambient>{r} {g} {b} {a}</ambient><diffuse>{r} {g} {b} {a}</diffuse>
            {f'<specular>{spec}</specular>' if spec else ''}
          </material>
        </visual>
      </link>
"""
    return s


def box(x, y, z):
    return f"<box><size>{x} {y} {z}</size></box>"


def build(water_h, camera=False):
    parts = []
    # collection basin / tank
    parts.append(vis("tank_basin", "0 0 0.06 0 0 0", box(0.95, 0.95, 0.12), (0.10, 0.45, 0.55, 1)))
    # condensate water (grows with water_h)
    if water_h > 0.001:
        zc = 0.12 + water_h / 2.0
        parts.append(vis("water", f"0 0 {zc:.4f} 0 0 0", box(0.86, 0.86, water_h),
                         (0.10, 0.55, 0.95, 1), transparency=0.25))
    # legs holding the gel cube above the basin
    for sx, sy, nm in ((0.22, 0.22, "lf"), (-0.22, 0.22, "lb"), (0.22, -0.22, "rf"), (-0.22, -0.22, "rb")):
        parts.append(vis(f"leg_{nm}", f"{sx} {sy} 0.27 0 0 0", box(0.04, 0.04, 0.30), (0.2, 0.2, 0.22, 1)))
    # inner silica-gel adsorbent cube
    parts.append(vis("gel_cube", "0 0 0.55 0 0 0", box(0.6, 0.6, 0.5), (0.12, 0.40, 0.85, 1)))
    # outer transparent glass enclosure: 4 walls + top
    glass = (0.55, 0.70, 0.85, 1)
    parts.append(vis("wall_front", "0 -0.5 0.57 0 0 0", box(1.0, 0.03, 1.04), glass, transparency=0.68, spec="0.4 0.5 0.6 1"))
    parts.append(vis("wall_back",  "0 0.5 0.57 0 0 0",  box(1.0, 0.03, 1.04), glass, transparency=0.68, spec="0.4 0.5 0.6 1"))
    parts.append(vis("wall_left",  "-0.5 0 0.57 0 0 0", box(0.03, 1.0, 1.04), glass, transparency=0.68, spec="0.4 0.5 0.6 1"))
    parts.append(vis("wall_right", "0.5 0 0.57 0 0 0",  box(0.03, 1.0, 1.04), glass, transparency=0.68, spec="0.4 0.5 0.6 1"))
    parts.append(vis("glass_top",  "0 0 1.10 0 0 0",    box(1.0, 1.0, 0.03), glass, transparency=0.72, spec="0.4 0.5 0.6 1"))
    # stack chimney for night natural-convection ventilation (keeps u >~ 0.02 m/s) + cap
    parts.append(vis("chimney", "0 0 1.34 0 0 0",
                     "<cylinder><radius>0.06</radius><length>0.46</length></cylinder>", (0.30, 0.30, 0.33, 1)))
    parts.append(vis("chimney_cap", "0 0 1.585 0 0 0",
                     "<cylinder><radius>0.10</radius><length>0.03</length></cylinder>", (0.22, 0.22, 0.24, 1)))
    # low intake louvres (open at night for the stack effect, damped shut by day)
    for vx, vy, sx, sy, nm in ((0, -0.505, 0.34, 0.02, "f"), (0, 0.505, 0.34, 0.02, "b"),
                               (-0.505, 0, 0.02, 0.34, "l"), (0.505, 0, 0.02, 0.34, "r")):
        parts.append(vis(f"vent_{nm}", f"{vx} {vy} 0.22 0 0 0", box(sx, sy, 0.12), (0.12, 0.12, 0.14, 1)))

    cam = ""
    if camera:
        cam = """    <model name="shot_camera">
      <static>true</static>
      <pose>2.9 -2.9 2.15 0 0.40 2.356</pose>
      <link name="link">
        <sensor name="shot_cam" type="camera">
          <always_on>1</always_on><update_rate>4</update_rate><visualize>false</visualize>
          <camera>
            <horizontal_fov>1.0</horizontal_fov>
            <image><width>1500</width><height>1000</height><format>R8G8B8</format></image>
            <clip><near>0.05</near><far>100</far></clip>
            <save enabled="true"><path>/tmp/awhfill</path></save>
          </camera>
        </sensor>
      </link>
    </model>
"""
    body = "".join(parts)
    return f"""<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="awh_cube">
    <light name="sun" type="directional">
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.95 0.95 0.92 1</diffuse><specular>0.25 0.25 0.25 1</specular>
      <direction>-0.4 0.3 -0.9</direction>
    </light>
    <model name="ground"><static>true</static><link name="l">
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>50 50</size></plane></geometry>
        <material><ambient>0.72 0.72 0.74 1</ambient><diffuse>0.78 0.78 0.80 1</diffuse></material></visual>
    </link></model>
    <scene><ambient>0.55 0.55 0.55 1</ambient><background>0.86 0.91 0.97 1</background><shadows>true</shadows></scene>
    <model name="awh_cube">
      <static>true</static>
{body}    </model>
{cam}  </world>
</sdf>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--water", type=float, default=0.05)
    ap.add_argument("--camera", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    open(a.out, "w").write(build(a.water, a.camera))
    print(f"wrote {a.out}  (water_h={a.water}, camera={a.camera})")


if __name__ == "__main__":
    main()
