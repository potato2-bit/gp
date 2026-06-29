#!/usr/bin/env python3
"""
rail_guided_recalc.py - sizing for the rail-guided, full-width-brush variant.

The robot changed from a free diff-drive crawler (0.25 m brush, boustrophedon)
to a rail-guided carriage (full panel-width brush, fall-line sweeps). This
recomputes the parameters that the change touches: brush, rail drive, coverage
time, rail/rack length. TEC AWG, tank, power and sensors are unchanged.

Writes output/rail_guided_design.json.
"""
import json, math
from pathlib import Path

g = 9.81
# ---- panel / demonstrator ----
panel_w = 1.0          # m, panel width (brush spans this)
panel_L = 2.0          # m, slope length (sweep travel)
tilt_deg = 24.0
tilt = math.radians(tilt_deg)
L_per_m2 = 0.3         # L per m2 per event (microfibre robot, was 1.8 wet-wash)
area = panel_w * panel_L

# ---- carriage ----
M = 8.0                # kg, rail carriage (heavier than the 6 kg crawler:
                       #     full-width brush + rail bogies)
mu_roll = 0.05         # rolling resistance of guide wheels on rail
v_clean = 0.06         # m/s sweep speed (demo); design clean speed 0.05

# ---- full-width brush ----
brush_len = 0.96       # m, spans the 1 m panel (with frame margin)
brush_dia = 0.05       # m, roller outer (microfibre over PVC core)
brush_rpm = 100.0
brush_mass = 1.0       # kg (1 m PVC core + microfibre + 2 bearings + shaft)
# contact drag torque: soft low-pressure microfibre. Normal line load ~6 N/m,
# friction coeff brush-glass ~0.3, acts at roller radius.
line_load = 6.0        # N/m of contact
mu_brush = 0.30
F_brush = line_load * brush_len * mu_brush      # tangential drag force
T_brush = F_brush * (brush_dia / 2.0)           # roller torque
T_brush_motor = T_brush * 1.5                   # 1.5 safety factor
brush_w_rads = brush_rpm * 2 * math.pi / 60.0
P_brush = T_brush * brush_w_rads                # mechanical W

# ---- rail drive (carriage up the 24 deg slope) ----
F_grav = M * g * math.sin(tilt)
F_roll = M * g * mu_roll * math.cos(tilt)
F_drag_clean = F_brush                          # brush reaction on the carriage
F_drive = F_grav + F_roll + F_drag_clean        # worst case: climbing + cleaning
# rack-and-pinion, pinion pitch dia 30 mm, one drive motor (single rail) with
# the second rail idling, or split over two; size for the single-motor worst case
pinion_dia = 0.030
T_pinion = F_drive * (pinion_dia / 2.0)
T_drive_motor = T_pinion * 1.5                  # 1.5 SF
drive_rpm = v_clean / (math.pi * pinion_dia) * 60.0
P_drive = F_drive * v_clean                     # mechanical W

# ---- coverage time / throughput ----
t_down = panel_L / v_clean
t_up = panel_L / v_clean
t_panel = t_down + t_up                         # one clean (down) + return (up)
water_per_event = L_per_m2 * area

# ---- rail + rack hardware ----
rail_len = panel_L + 0.4                         # travel + carriage + over-run
n_rails = 2
rack_len = rail_len * n_rails

out = {
    "panel": {"width_m": panel_w, "slope_len_m": panel_L, "tilt_deg": tilt_deg, "area_m2": area},
    "carriage_mass_kg": M,
    "brush": {
        "length_m": brush_len, "dia_m": brush_dia, "rpm": brush_rpm, "mass_kg": brush_mass,
        "drag_force_N": round(F_brush, 2), "roller_torque_Nm": round(T_brush, 3),
        "motor_torque_req_Nm": round(T_brush_motor, 3), "mech_power_W": round(P_brush, 1),
    },
    "rail_drive": {
        "F_gravity_N": round(F_grav, 2), "F_roll_N": round(F_roll, 2),
        "F_clean_drag_N": round(F_drag_clean, 2), "F_drive_total_N": round(F_drive, 2),
        "pinion_dia_m": pinion_dia, "motor_torque_req_Nm": round(T_drive_motor, 3),
        "drive_rpm": round(drive_rpm, 1), "mech_power_W": round(P_drive, 1),
        "v_clean_mps": v_clean,
    },
    "coverage": {
        "t_down_s": round(t_down, 1), "t_return_s": round(t_up, 1),
        "t_per_panel_s": round(t_panel, 1), "water_per_event_L": round(water_per_event, 2),
        "note": "full-width single sweep vs ~230 s boustrophedon for the 0.25 m crawler",
    },
    "rails": {"rail_len_m": round(rail_len, 2), "n_rails": n_rails, "rack_len_total_m": round(rack_len, 2)},
}
Path("output").mkdir(exist_ok=True)
Path("output/rail_guided_design.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
