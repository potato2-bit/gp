"""
Power and control finalization for the rail-guided TEC PV-cleaning robot.
Computes exact electrical numbers, weight closure, and 48 V dock string config.
All inputs traced to output/rail_guided_design.json and ELECTRICAL_DESIGN.tex.
"""
import math

g = 9.81
V = 12.0

# ---------------- DRIVE MOTOR ----------------
# Committed: GA25-370 12 V, 1:71 reduction variant ("60 rpm") with quadrature encoder.
# This keeps the output near 60 rpm no-load (so 38 rpm sits at a healthy ~0.64 duty
# with load droop headroom) while the 1:71 reduction still resists back-driving far
# better than the 250 rpm buy-list part. Stall torque 0.78 N.m (8 kgf.cm).
no_load_rpm   = 60.0    # mfr typical for ~1:71 GA25-370 at 12 V
rated_rpm     = 48.0
stall_torque  = 0.78    # N.m (8 kgf.cm)
rated_torque  = 0.27    # N.m
rated_current = 0.42    # A
stall_current = 1.50    # A
no_load_current = 0.07  # A

kt = stall_torque / stall_current
T_trac = 0.838
T_load = T_trac / 2.0
I_op   = T_load / kt
I_op_two = 2 * I_op

print("=== DRIVE MOTOR (GA25-370 1:71 '60 rpm', 12 V, encoder) ===")
print(f"kt (output)        = {kt:.3f} N.m/A")
print(f"T_load per rail    = {T_load:.3f} N.m")
print(f"I_op per motor     = {I_op:.3f} A")
print(f"I_op two motors    = {I_op_two:.3f} A  ->  {I_op_two*V:.1f} W")
print(f"rated current/mtr  = {rated_current} A  ; stall current/mtr = {stall_current} A")
print(f"torque margin/mtr  = {stall_torque/T_load:.2f}x")
print(f"speed margin       = {no_load_rpm/38.2:.2f}x")
D_drive = 38.2 / no_load_rpm
print(f"PWM duty @38.2 rpm = {D_drive:.2f}")

# ---------------- HOLD CHECK ----------------
m = 8.0
tilt = math.radians(24)
F_g = m * g * math.sin(tilt)
r_pin = 0.015
T_back_total = F_g * r_pin
print("\n=== HOLD ON TILT (unpowered) ===")
print(f"F_gravity along slope = {F_g:.2f} N")
print(f"back-drive torque at pinion total = {T_back_total:.3f} N.m, per rail = {T_back_total/2:.3f} N.m")
print("GA25 spur/planetary gearbox is NOT self-locking; 1:90 raises reflected")
print("friction but cannot be trusted to hold 0.25 N.m/rail. -> driver active brake")
print("(short windings) + sprung park detent. Worm-gear alternative noted.")

# ---------------- DRIVER ----------------
print("\n=== DRIVER SELECTION ===")
print("Rules: cont >= 1.5*I_op, peak >= I_stall, Vmax >= 1.3*Vsupply(=15.6 V)")
print("TB6612FNG: Vmot ceiling 13.5 V < 15.6 V -> FAILS voltage rule.")
print("DRV8833: 10.8 V -> fails worse.")
print("Committed: Cytron MDD3A dual-channel, 3 A cont / 5 A peak, 5-30 V.")
cont2, peak2, Vmax2 = 3.0, 5.0, 30.0
print(f"  cont {cont2} >= 1.5*I_op {1.5*I_op:.2f}  -> {cont2>=1.5*I_op}")
print(f"  peak {peak2} >= I_stall {stall_current} -> {peak2>=stall_current}")
print(f"  Vmax {Vmax2} >= 1.3*12 {1.3*12:.1f}     -> {Vmax2>=1.3*12}")
print(f"  headroom cont/I_op = {cont2/I_op:.1f}x  (old BTS7960 43 A = {43/I_op:.0f}x absurd)")
print("  One MDD3A drives BOTH drive motors (dual channel), supports active brake.")

# ---------------- BRUSH MOTOR ----------------
print("\n=== BRUSH MOTOR ===")
brush_stall, brush_stall_I = 0.78, 1.6
brush_kt = brush_stall / brush_stall_I
I_brush_steady = 0.065 / brush_kt
print(f"GA25-370 100 rpm variant; steady I = {I_brush_steady:.2f} A, inrush ~{brush_stall_I} A")
print("One direction only -> low-side logic-level N-MOSFET switch (IRLZ44N).")

# ---------------- PUMP ----------------
print("\n=== PUMP ===")
I_pump = 3.75
print(f"12 V diaphragm pump, I ~ {I_pump} A -> {I_pump*12:.0f} W. Switch: IRLZ44N low-side MOSFET.")

# ---------------- DOCK 48 V STRINGS ----------------
print("\n=== DOCK 48 V STRING CONFIG ===")
V_tile, N, P_tile = 13.3, 38, 79.8
P_array = N * P_tile
Vstring = 4 * V_tile
I_string = 6.0
print(f"P_array = {P_array:.0f} W")
print(f"series-quad string V = 4*13.3 = {Vstring:.1f} V (48 V nominal bus)")
print(f"38 / 4 = {38/4} -> not integer.")
print("Config: 9 quads (36 tiles) + 1 series-pair (2 tiles).")
print(f"  each quad string current = {I_string} A ; pair string current = {I_string} A")
print(f"  ideal bus current = P/V = {P_array/48:.1f} A  (vs 228 A at 12 V)")
print(f"  with converter loss allowance ~ 63 A (matches ELECTRICAL_DESIGN).")
print("per-string MOSFET: a string seen open holds up to ~53 V -> need >=2x =106 V")
print("  and >=2x string current = 12 A. Commit IRLB4030 (100 V, logic-level, 180 A).")
print(f"  switch count = 9 + 1 = 10 (one per string).")

# ---------------- DOCK MPPT ----------------
print("\n=== DOCK MPPT (48 V) ===")
P_pv = 1416.0
I_charge = P_pv / 48
print(f"PV {P_pv:.0f} Wp at 48 V bus -> charge current ~ {I_charge:.0f} A")
print("One EPever Tracer4215AN (40 A, 150 V PV) covers it; replaces 3x 12 V MPPT.")

# ---------------- BATTERY ----------------
print("\n=== CARRIAGE BATTERY ===")
E_session = 23.2
E_usable_20 = 20 * 12 * 0.8 * 0.95
E_usable_10 = 10 * 12 * 0.8 * 0.95
print(f"12 V 20 Ah LFP: usable {E_usable_20:.0f} Wh, sessions = {E_usable_20/E_session:.1f}, weight ~2.3 kg")
print(f"12 V 10 Ah LFP: usable {E_usable_10:.0f} Wh, sessions = {E_usable_10/E_session:.1f}, weight ~1.3 kg")
I_peak = 92.7/12
print(f"  peak draw {I_peak:.1f} A = {I_peak/10:.2f}C on 10 Ah pack (BMS 15-20 A ok).")

# ---------------- WEIGHT BUDGET ----------------
def budget(batt_label, batt_mass):
    items = {
     "Carriage base plate (Al 6061 3mm)": 1.10,
     "Full-width brush 0.96 m": 1.00,
     "Carriage side-frames (2)": 0.80,
     "V-groove wheels x8 + bogie plates": 0.40,
     "Drive motors 2x GA25-370": 0.21,
     "Steel pinions 2x O30 M1": 0.06,
     "Brush motor GA25-370": 0.105,
     "Driver MDD3A + 2 MOSFET switches": 0.05,
     "Water pump (diaphragm)": 0.30,
     batt_label: batt_mass,
     "ESP32 DevKit": 0.010,
     "Raspberry Pi 4B + heatsink": 0.055,
     "Sensors + 2 limit switches": 0.10,
     "Cabling, connectors, fuses": 0.30,
     "Tank dry + spray bar + nozzles + tube": 0.40,
     "Water mean fill (1.8 L)": 1.80,
    }
    tot = sum(items.values())
    for k, v in items.items():
        print(f"  {k:42s} {v:5.2f}")
    print(f"  {'TOTAL':42s} {tot:5.2f} kg   (target 8.00, delta {tot-8.0:+.2f})")
    return tot

print("\n=== CARRIAGE WEIGHT BUDGET (TEC moved to dock) ===")
print("(A) with real 20 Ah battery (2.3 kg):")
tot20 = budget("Battery 12V 20Ah LFP (real)", 2.30)
print("\n(B) FIX: 10 Ah battery (1.3 kg) + dock top-up charging:")
tot10 = budget("Battery 12V 10Ah LFP (real)", 1.30)

print("\n=== CLOSURE FLAG ===")
print(f"Old CAD budget closed at 8.00 with TEC 1.05 ON carriage and battery hidden in 0.37 'elec bay'.")
print(f"Real 20 Ah LFP is ~2.3 kg, not 0.37 -> the carriage cannot hold TEC + 20 Ah and stay <=8 kg.")
print(f"Two corrections close it: (1) TEC is a STATIONARY DOCK now, so its 1.05 kg leaves the carriage;")
print(f"  (2) drop the pack to 12 V 10 Ah LFP (~1.3 kg, still {E_usable_10/E_session:.0f} sessions),")
print(f"  topped up at the dock between cleans. Result: {tot10:.2f} kg, inside 8.0 kg.")
