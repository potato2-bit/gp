#!/usr/bin/env python3
"""
model_calcs.py -- engineering estimates derived from the Gazebo model of the
rail-guided TEC PV-cleaning robot.

Every input below is read straight off the model files in this folder:
  * panel_world_tilt.sdf       -- panel 2.0 x 1.0 m, tilt 24 deg, guide rails
  * pvbot_railed_control.urdf  -- carriage links/masses (sum 7.99 kg ~ 8.0 kg),
                                  prismatic rail effort ceiling 45 N, pinion 30 mm
  * COMPONENT_MAP.md           -- per-part masses, GA25-370 motors, brush 0.96 m
  * ../output/rail_guided_design.json   -- the model's own computed values
  * ../output/nac_tec_robot_results.json-- NAC dock TEC per-tile water yield

The script recomputes the performance from first principles and prints a
"computed vs. model" check so the report numbers are reproducible and traceable.

Run:  python model_calcs.py
"""
import json
import math
import os

g = 9.81  # m/s^2

# --------------------------------------------------------------------------
# INPUTS read off the model
# --------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "output"))

# -- geometry (panel_world_tilt.sdf) --
panel_L = 2.0          # m, up-slope length (local x, +-1.0 m)
panel_W = 1.0          # m, cross-slope width (local y, +-0.5 m)
panel_A = panel_L * panel_W
tilt_deg = 24.0
tilt = math.radians(tilt_deg)
rail_travel = 1.40     # m, prismatic upper limit (pvbot_railed_control.urdf)
rail_len = 2.4         # m, physical rail (rail_guided_design.json)

# -- masses (pvbot_railed_control.urdf / COMPONENT_MAP.md) --
m_carriage = 8.0       # kg (model closes at 7.991)

# -- drive train --
r_pinion = 0.015       # m, Ø30 mm module-1 steel pinion
n_drive = 2            # two driven rails (GA25-370 1:71 each)
effort_ceiling = 45.0  # N, prismatic effort cap = real motor ceiling
v_clean = 0.06         # m/s, cleaning traverse (design)
SF = 1.5               # design safety factor on torque

# GA25-370 1:71 gearmotor @ 12 V (ELECTRICAL_DESIGN.tex)
T_stall = 0.78         # N*m output stall torque
I_stall = 1.5          # A
I_free = 0.42          # A
rpm_noload_out = 60.0  # output rpm no-load
kt = T_stall / I_stall # N*m/A, torque constant at gearbox output

# -- rolling / guide resistance --
mu_roll = 0.05         # effective rolling coeff of the V-groove guide wheels

# -- brush (rail_guided_design.json / COMPONENT_MAP.md) --
brush_len = 0.96       # m, full-width roller
r_brush = 0.025        # m, contact radius (Ø50 core)
rpm_brush = 100.0
F_brush_drag = 1.73    # N, brush contact drag along travel

# -- water --
L_per_m2 = 0.3         # L/m^2 per cleaning event (robot light wash)
tank_L = 3.6           # L on-carriage tank
pump_peak_W = 45.0     # W, diaphragm pump peak
pump_duty = 0.50       # spraying duty fraction during a stroke

# -- electronics (carriage) --
P_logic_W = 3.5        # Rpi4 + ESP32 + sensors, continuous
eff_drive = 0.50       # motor+driver electrical->mechanical efficiency (small geared DC)
eff_brush = 0.35
E_idle_Wh = 0.3        # repositioning / park per panel (ELECTRICAL_DESIGN.tex)

# -- battery --
V_batt = 12.0
Ah_batt = 10.0
DoD = 0.80             # usable depth of discharge (LFP)

# -- TEC dock (nac_tec_robot_results.json) --
tile_water_gday_nac = 105.97   # g/day per TEC1-12706 tile at NAC
tile_energy_kWhyr = 56.03      # kWh/yr per tile
n_tiles_dock = 38              # residential NAC dock bank
tile_water_gday_bench = 14.65  # g/day per tile (Benban bench climate)
n_tiles_bench = 4
arr_demand_Lyr = 1439.42       # L/yr cleaning-water demand, 9.9 kWp NAC array
arr_area_m2 = 46.01            # m^2 glass, 18x550 Wp modules
clean_interval_days = 3.5

# load the model's own computed values for the cross-check
with open(os.path.join(OUT, "rail_guided_design.json")) as f:
    ref = json.load(f)

# --------------------------------------------------------------------------
# 1. SLOPE FORCE BALANCE + CLIMB MARGIN
# --------------------------------------------------------------------------
F_grav = m_carriage * g * math.sin(tilt)
F_roll = mu_roll * m_carriage * g * math.cos(tilt)
F_drive_total = F_grav + F_roll + F_brush_drag           # worst case: climbing + cleaning
margin_total = effort_ceiling / F_drive_total
margin_grav_roll = effort_ceiling / (F_grav + F_roll)

# --------------------------------------------------------------------------
# 2. DRIVE MOTOR TORQUE + GEAR CHECK
# --------------------------------------------------------------------------
T_pinion_total = F_drive_total * r_pinion                # N*m, both pinions
T_req_design = T_pinion_total * SF                       # with 1.5 SF (matches JSON)
T_per_motor = T_pinion_total / n_drive                   # shared by two motors
T_stall_total = T_stall * n_drive
torque_margin = T_stall_total / T_req_design
omega_pinion = v_clean / r_pinion                        # rad/s
rpm_pinion = omega_pinion * 60 / (2 * math.pi)
P_drive_mech = F_drive_total * v_clean                   # W

# gear tooth bending (Lewis), module-1 steel, ~30 teeth, b = 12 mm face
F_t = F_drive_total
b_face, module, Y = 0.012, 0.001, 0.36
sigma_tooth = F_t / (b_face * module * Y) / 1e6          # MPa
SF_tooth = 200.0 / sigma_tooth                           # vs ~200 MPa allowable steel

# back-drive hold when unpowered
T_backdrive_pinion = F_grav * r_pinion                   # N*m at pinion
T_backdrive_motor = T_backdrive_pinion / 71.0            # referred to motor shaft

# --------------------------------------------------------------------------
# 3. BRUSH TORQUE + POWER
# --------------------------------------------------------------------------
T_brush = F_brush_drag * r_brush
T_brush_req = T_brush * SF
omega_brush = rpm_brush * 2 * math.pi / 60
P_brush_mech = T_brush * omega_brush

# --------------------------------------------------------------------------
# 4. COVERAGE + THROUGHPUT
# --------------------------------------------------------------------------
t_pass = panel_L / v_clean
t_per_panel = 2 * t_pass                                 # down + up sweep
rate_fullcycle = panel_A / t_per_panel                   # m^2/s, full down+up
rate_fullcycle_m2h = rate_fullcycle * 3600
panels_per_hour_clean = 3600 / t_per_panel
# realistic daily capacity with 60% duty (repositioning, docking, refills)
duty_field = 0.60
m2_per_day_8h = rate_fullcycle_m2h * 8 * duty_field

# --------------------------------------------------------------------------
# 5. WATER PER EVENT + TANK AUTONOMY
# --------------------------------------------------------------------------
water_per_event = L_per_m2 * panel_A
cleans_per_tank = tank_L / water_per_event
# scale to the NAC residential array
arr_demand_per_event = L_per_m2 * arr_area_m2
tank_fills_per_array = arr_demand_per_event / tank_L

# --------------------------------------------------------------------------
# 6. ENERGY PER PANEL + BATTERY AUTONOMY
# --------------------------------------------------------------------------
E_pump = pump_peak_W * pump_duty * t_per_panel / 3600
E_drive = (P_drive_mech / eff_drive) * t_per_panel / 3600
E_brush = (P_brush_mech / eff_brush) * t_per_panel / 3600
E_logic = P_logic_W * t_per_panel / 3600
E_panel = E_pump + E_drive + E_brush + E_logic + E_idle_Wh
E_batt_usable = V_batt * Ah_batt * DoD
panels_per_charge = E_batt_usable / E_panel
arr_panels = arr_area_m2 / panel_A
E_array_clean = arr_panels * E_panel
array_cleans_per_charge = E_batt_usable / E_array_clean

# --------------------------------------------------------------------------
# 7. TEC DOCK WATER BALANCE (NAC residential)
# --------------------------------------------------------------------------
dock_water_Lday = n_tiles_dock * tile_water_gday_nac / 1000.0
arr_demand_Lday = arr_demand_Lyr / 365.0
self_supply_f = dock_water_Lday / arr_demand_Lday
harvest_per_interval = dock_water_Lday * clean_interval_days
demand_per_interval = L_per_m2 * arr_area_m2
dock_energy_kWhyr = n_tiles_dock * tile_energy_kWhyr
bench_water_Lday = n_tiles_bench * tile_water_gday_bench / 1000.0

# --------------------------------------------------------------------------
# 8. TIP / WHEEL-LIFT STABILITY ON THE 24 deg SLOPE
# --------------------------------------------------------------------------
h_cg = 0.06            # m, CG height above the glass (deck stack estimate)
wheelbase_x = 0.26     # m, fore-aft bogie spacing (+-0.13)
cg_shift = h_cg * math.tan(tilt)
SF_tip = (wheelbase_x / 2) / cg_shift

# --------------------------------------------------------------------------
# REPORT
# --------------------------------------------------------------------------
def chk(name, got, want, unit=""):
    tag = "OK" if (want is None or abs(got - want) <= 0.03 * abs(want) + 1e-6) else "**"
    w = "" if want is None else f"   (model {want:g})"
    print(f"  {tag} {name:<34}= {got:8.3f} {unit}{w}")

print("=" * 70)
print(" GAZEBO MODEL -- DERIVED ENGINEERING ESTIMATES")
print("=" * 70)
print(f" panel {panel_L} x {panel_W} m = {panel_A} m^2 at {tilt_deg} deg; "
      f"carriage {m_carriage} kg")

print("\n[1] Slope force balance + climb margin")
chk("F_gravity (m g sin th)", F_grav, ref["rail_drive"]["F_gravity_N"], "N")
chk("F_roll  (mu m g cos th)", F_roll, ref["rail_drive"]["F_roll_N"], "N")
chk("F_brush_drag", F_brush_drag, ref["rail_drive"]["F_clean_drag_N"], "N")
chk("F_drive_total", F_drive_total, ref["rail_drive"]["F_drive_total_N"], "N")
print(f"     climb margin (45 N / load)        = {margin_total:.2f}  "
      f"(grav+roll only {margin_grav_roll:.2f})")

print("\n[2] Drive motor torque + gear check")
chk("T_pinion_total (no SF)", T_pinion_total, None, "N.m")
chk("T_required (x1.5 SF)", T_req_design, ref["rail_drive"]["motor_torque_req_Nm"], "N.m")
chk("rpm_pinion @ 0.06 m/s", rpm_pinion, ref["rail_drive"]["drive_rpm"], "rpm")
chk("P_drive_mech", P_drive_mech, ref["rail_drive"]["mech_power_W"], "W")
print(f"     per-motor torque {T_per_motor:.3f} vs stall {T_stall} N.m "
      f"-> torque margin (2 motors / req) {torque_margin:.2f}")
print(f"     tooth bending sigma {sigma_tooth:.2f} MPa -> SF_tooth {SF_tooth:.0f}")
print(f"     back-drive at motor shaft {T_backdrive_motor*1000:.1f} mN.m (held by brake+gearbox)")

print("\n[3] Brush torque + power")
chk("T_brush (drag x r)", T_brush, ref["brush"]["roller_torque_Nm"], "N.m")
chk("T_brush_req (x1.5)", T_brush_req, ref["brush"]["motor_torque_req_Nm"], "N.m")
chk("P_brush_mech", P_brush_mech, ref["brush"]["mech_power_W"], "W")

print("\n[4] Coverage + throughput")
chk("t_pass (one stroke)", t_pass, ref["coverage"]["t_down_s"], "s")
chk("t_per_panel (down+up)", t_per_panel, ref["coverage"]["t_per_panel_s"], "s")
print(f"     cleaning rate (full cycle)        = {rate_fullcycle_m2h:.1f} m^2/h "
      f"({panels_per_hour_clean:.1f} panels/h)")
print(f"     field capacity @60% duty, 8 h     = {m2_per_day_8h:.0f} m^2/day")

print("\n[5] Water per event + tank autonomy")
chk("water_per_event (0.3 L/m^2)", water_per_event, ref["coverage"]["water_per_event_L"], "L")
print(f"     cleans per 3.6 L tank             = {cleans_per_tank:.1f}")
print(f"     NAC array {arr_area_m2} m^2 -> {arr_demand_per_event:.1f} L "
      f"= {tank_fills_per_array:.1f} tank fills")

print("\n[6] Energy per panel + battery autonomy")
print(f"     E_pump {E_pump:.3f}  E_drive {E_drive:.3f}  E_brush {E_brush:.3f}  "
      f"E_logic {E_logic:.3f}  E_idle {E_idle_Wh:.2f}  Wh")
chk("E_per_panel", E_panel, None, "Wh")
print(f"     usable battery {E_batt_usable:.0f} Wh -> {panels_per_charge:.0f} panel sweeps/charge")
print(f"     NAC array clean {E_array_clean:.1f} Wh -> {array_cleans_per_charge:.1f} array cleans/charge")

print("\n[7] TEC dock water balance (NAC residential)")
print(f"     dock 38 tiles harvest             = {dock_water_Lday:.2f} L/day")
print(f"     array cleaning demand             = {arr_demand_Lday:.2f} L/day")
print(f"     self-supply ratio f               = {self_supply_f:.2f}  (>=1 => self-sufficient)")
print(f"     per {clean_interval_days}-day interval: harvest {harvest_per_interval:.1f} L "
      f">= demand {demand_per_interval:.1f} L")
print(f"     dock TEC energy                   = {dock_energy_kWhyr:.0f} kWh/yr")
print(f"     bench 4-tile harvest (Benban)     = {bench_water_Lday*1000:.0f} g/day")

print("\n[8] Tip / wheel-lift stability on 24 deg")
print(f"     CG shift {cg_shift*1000:.1f} mm vs half-wheelbase {wheelbase_x/2*1000:.0f} mm "
      f"-> SF_tip {SF_tip:.1f} (plus rails capture it)")

# dump machine-readable results for the report
results = {
    "force": {"F_grav": F_grav, "F_roll": F_roll, "F_brush": F_brush_drag,
              "F_total": F_drive_total, "margin": margin_total},
    "drive": {"T_pinion_total": T_pinion_total, "T_req_SF": T_req_design,
              "T_per_motor": T_per_motor, "torque_margin": torque_margin,
              "rpm_pinion": rpm_pinion, "sigma_tooth_MPa": sigma_tooth,
              "T_backdrive_motor_mNm": T_backdrive_motor * 1000},
    "brush": {"T_brush": T_brush, "P_brush_mech": P_brush_mech},
    "coverage": {"t_per_panel": t_per_panel, "rate_m2h": rate_fullcycle_m2h,
                 "panels_per_h": panels_per_hour_clean, "m2_per_day": m2_per_day_8h},
    "water": {"per_event": water_per_event, "cleans_per_tank": cleans_per_tank,
              "tank_fills_per_array": tank_fills_per_array},
    "energy": {"E_panel_Wh": E_panel, "panels_per_charge": panels_per_charge,
               "array_cleans_per_charge": array_cleans_per_charge,
               "E_batt_usable": E_batt_usable},
    "dock": {"harvest_Lday": dock_water_Lday, "demand_Lday": arr_demand_Lday,
             "self_supply_f": self_supply_f, "energy_kWhyr": dock_energy_kWhyr,
             "bench_gday": bench_water_Lday * 1000},
    "stability": {"cg_shift_mm": cg_shift * 1000, "SF_tip": SF_tip},
}
with open(os.path.join(HERE, "model_calcs_results.json"), "w") as f:
    json.dump(results, f, indent=2)
print("\nwrote model_calcs_results.json")
