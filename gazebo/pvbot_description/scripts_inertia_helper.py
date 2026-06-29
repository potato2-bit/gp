#!/usr/bin/env python3
"""
scripts_inertia_helper.py - compute the mass + inertia + placement table for
every CARRIAGE link of pvbot_railed_control.urdf, straight from the finalized
Option-B weight budget (ELECTRICAL_DESIGN.tex Table tab:weight / MARKET buy-list)
and the CAD dimensions (CAD_DESIGN_PACKAGE.tex).

Frame (matches the URDF base_link box 0.30 x 0.92 x 0.10):
  +X = down-slope / travel,  +Y = brush axis / panel width,  +Z = out of glass.
Origins below are relative to base_link centre.

Each entry: (link, mass_kg, shape, dims_m, xyz, rpy, note).
  box dims = (lx,ly,lz);  cyl dims = (radius, length) with rpy giving the axis.
Inertia: solid box  Ixx=m/12(y^2+z^2) etc;  solid cyl about its own axis.
We report the principal-axis inertia in the link's own visual frame; for the
cylinders we rotate so the reported ixx/iyy/izz line up with the URDF axes after
the rpy in the joint (we keep it simple: report cylinder inertia in the cylinder
local frame, which is what URDF <inertial> without an <origin rpy> expects when
the visual is rotated by the same rpy at the joint - good enough; all our
cylinders are placed via fixed joints with rpy so the inertia ellipsoid is
near-symmetric anyway).
"""
import math

# ------------------------------------------------------------------ box inertia
def box_I(m, lx, ly, lz):
    ixx = m / 12.0 * (ly * ly + lz * lz)
    iyy = m / 12.0 * (lx * lx + lz * lz)
    izz = m / 12.0 * (lx * lx + ly * ly)
    return ixx, iyy, izz

# solid cylinder, axis along local z (length=L, radius=r)
def cyl_I(m, r, L):
    irad = m * (3 * r * r + L * L) / 12.0   # about a transverse axis
    iax = 0.5 * m * r * r                    # about the cylinder axis
    return irad, irad, iax                   # ixx, iyy, izz(axis=z local)

# ------------------------------------------------------------------ the budget
# (link, mass, shape, dims, xyz, rpy, note)  -- Option B, TEC OFF carriage.
P = []
# 1. chassis base plate (Al 6061 3 mm) - the gantry beam itself = base_link.
#    URDF footprint 0.30 x 0.92, but the real structural plate is 0.40x0.30x0.003.
#    We keep base_link as the 0.30x0.92x0.10 gantry envelope (CAD GA 460x300; the
#    0.92 spans the rail gauge). Mass 1.10 kg (D-101).
P.append(("base_link", 1.100, "box", (0.30, 0.92, 0.10), (0,0,0), (0,0,0),
          "D-101 chassis base plate Al6061-T6 3mm; gantry beam envelope"))

# 2. two side-frames (2x) total 0.80 -> 0.40 each. Bridge deck edge to rails.
#    Plate ~ 0.34(x) x 0.02(y) x 0.12(z), one at each y end (just inside rails).
P.append(("side_frame_left", 0.400, "box", (0.34, 0.02, 0.12), (0.0, 0.455, -0.01), (0,0,0),
          "D-108 carriage side-frame (2x=0.80)"))
P.append(("side_frame_right", 0.400, "box", (0.34, 0.02, 0.12), (0.0, -0.455, -0.01), (0,0,0),
          "D-108 carriage side-frame (2x=0.80)"))

# 3. full-width brush 0.96 m, O50 core (visual O80 shell). mass 1.00 (D-103/D-110)
#    cylinder axis along Y. length 0.96, r 0.04. front of carriage.
P.append(("brush_link", 1.000, "cyl", (0.040, 0.96), (0.115, 0, -0.045), (-math.pi/2, 0, 0),
          "D-103/D-110 full-width brush 0.96 m O50 core"))

# 4. brush motor GA25-370 (O24.4 x 62 mm). 0.105 kg. on a side-frame at brush end.
P.append(("brush_motor", 0.105, "cyl", (0.0122, 0.062), (0.115, 0.49, -0.045), (-math.pi/2, 0, 0),
          "GA25-370 100rpm brush motor"))

# 5. two drive motors GA25-370 (O24.4 x 62). total 0.21 -> 0.105 each. at the
#    two driven rails (y=+-0.47), aligned to pinions, axis along Y.
P.append(("drive_motor_left", 0.105, "cyl", (0.0122, 0.062), (-0.05, 0.42, -0.03), (-math.pi/2, 0, 0),
          "GA25-370 1:71 drive motor (left rail)"))
P.append(("drive_motor_right", 0.105, "cyl", (0.0122, 0.062), (-0.05, -0.42, -0.03), (-math.pi/2, 0, 0),
          "GA25-370 1:71 drive motor (right rail)"))

# 6. two O30 steel pinions module-1 (O30 x 12). total 0.06 -> 0.03 each. mesh rack
#    at y=+-0.47, axis along Y.
P.append(("pinion_left", 0.030, "cyl", (0.015, 0.012), (-0.05, 0.47, -0.03), (-math.pi/2, 0, 0),
          "O30 M1 steel pinion (left, meshes +y rack)"))
P.append(("pinion_right", 0.030, "cyl", (0.015, 0.012), (-0.05, -0.47, -0.03), (-math.pi/2, 0, 0),
          "O30 M1 steel pinion (right, meshes -y rack)"))

# 7. driver box: MDD3A (37x37) + 2 IRLZ44N MOSFETs. 0.05 kg. small box on deck.
P.append(("driver_box", 0.050, "box", (0.045, 0.045, 0.022), (-0.10, 0.15, 0.072), (0,0,0),
          "Cytron MDD3A + 2x IRLZ44N (D-106 elec bay)"))

# 8. water pump diaphragm (90x40x35). 0.30 kg. behind tank.
P.append(("water_pump", 0.300, "box", (0.090, 0.040, 0.035), (0.075, 0.16, 0.075), (0,0,0),
          "12V diaphragm pump 3.8 L/min (D-105)"))

# 9. tank + spray bar + nozzles + tube DRY = 0.40 ; water mean fill = 1.80.
#    Model as a tank link carrying dry 0.40 + water 1.80 = 2.20 kg, internal
#    166x226x96 mm. (We fold water into the tank link mass so the budget closes.)
P.append(("tank_link", 2.200, "box", (0.166, 0.226, 0.096), (0.07, 0, 0.098), (0,0,0),
          "D-105 HDPE tank 3.6L (dry 0.40 incl spray/nozzles) + 1.80 water mean fill"))

# 10. spray bar 0.96 m O24 + 9 nozzles. mass folded into tank dry (0.40) above, but
#     we give the bar a small visual link with token mass already counted -> 0.0
#     to avoid double counting. We instead show it with ~0 mass? No: keep budget
#     honest. The 0.40 "tank dry + spray bar + nozzles + tube" is ONE line. So the
#     spray bar visual must carry 0 added mass. Use 0.001 token, subtract from tank.
P.append(("spray_bar", 0.001, "cyl", (0.012, 0.92), (0.16, 0, -0.04), (-math.pi/2, 0, 0),
          "spray bar 0.96 m + 9 nozzles (mass in tank-dry line)"))

# 11. battery 12V 10Ah LFP ~1.30 kg. typical 10Ah LFP brick ~ 150x100x95 mm.
P.append(("battery", 1.300, "box", (0.150, 0.100, 0.095), (-0.06, -0.16, 0.085), (0,0,0),
          "12V 10Ah LFP pack 1.30 kg (15A BMS)"))

# 12. ESP32 DevKit (~58x28x13). 0.010 kg.
P.append(("esp32", 0.010, "box", (0.058, 0.028, 0.013), (-0.10, 0.06, 0.066), (0,0,0),
          "ESP32 DevKit real-time MCU"))

# 13. Raspberry Pi 4B + heatsink (85x56x20). 0.055 kg.
P.append(("rpi4", 0.055, "box", (0.085, 0.056, 0.020), (-0.10, -0.02, 0.070), (0,0,0),
          "Raspberry Pi 4B ROS2 host + heatsink"))

# 14. sensor cluster: DHT22, 2x DS18B20, INA219, MPU-6050, 2 limit switches.
#     0.10 kg total. one small box (cluster) + we add small marker boxes inside
#     visual only. Mass on the cluster link.
P.append(("sensor_cluster", 0.100, "box", (0.060, 0.040, 0.020), (-0.10, 0.30, 0.070), (0,0,0),
          "DHT22 + 2x DS18B20 + INA219 + MPU-6050 + 2 limit switches"))

# 15. cabling, connectors, fuses 0.30 kg - distributed; model as a thin tray.
P.append(("wiring_tray", 0.300, "box", (0.20, 0.30, 0.010), (-0.02, 0, 0.056), (0,0,0),
          "cabling, connectors, fuses (distributed)"))

# 16. V-groove wheels x8 + bogie plates 0.40 kg -> 4 bogies of 0.10 (2 wheels each).
for sx, sy, nm in [(0.13,0.45,"fr"), (-0.13,0.45,"rr"), (0.13,-0.45,"fl"), (-0.13,-0.45,"rl")]:
    P.append((f"bogie_{nm}", 0.100, "box", (0.06, 0.03, 0.05), (sx, sy, -0.045), (0,0,0),
              "OpenBuilds mini V-gantry bogie + 2 V-wheels (8 wheels/4 bogies=0.40)"))

# ------------------------------------------------------------------ report
total = 0.0
print("%-18s %7s  %-5s %-22s %-26s" % ("link","mass","shape","dims(m)","inertia ixx,iyy,izz"))
for (lk, m, sh, d, xyz, rpy, note) in P:
    total += m
    if sh == "box":
        I = box_I(m, *d)
        dims = "%.3f x %.3f x %.3f" % d
    else:
        I = cyl_I(m, *d)
        dims = "r=%.4f L=%.3f" % d
    print("%-18s %7.3f  %-5s %-22s %.3e %.3e %.3e" % (lk, m, sh, dims, *I))

print("-"*90)
print("CARRIAGE TOTAL (incl. 1.80 water in tank) = %.3f kg   target 8.00  delta %+0.3f" %
      (total, total - 8.00))
print("within +-3%% (7.76..8.24): %s" % ("YES" if 7.76 <= total <= 8.24 else "NO"))
