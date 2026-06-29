#!/usr/bin/env python3
"""
rack_pinion_drive.py - size the rack-and-pinion drive from the actual motor.

Answers "can the real motor + gear ratio climb the 24 deg rail?" by turning the
GA25-370 / 1:71 / Ø30 mm pinion into a linear force at the rail and comparing it
to the load. This is why a rack-and-pinion works where friction wheels did not:
the force is positive (geared), not limited by wheel-glass traction.
"""
import math

g = 9.81
# ---- drivetrain (committed parts) ----
T_stall_motor = 0.78      # N.m, GA25-370 12 V 1:71 stall torque (per motor)
T_rated_motor = 0.34      # N.m, ~continuous (≈ 44% stall, thermal-safe)
n_motors = 2              # two driven rails
rpm_noload = 60.0         # output rpm at 1:71
pinion_d = 0.030          # m, Ø30 mm pitch pinion
r = pinion_d / 2.0

# ---- carriage / rail ----
m = 8.0                   # kg, gantry carriage
tilt = math.radians(24.0)
mu_roll = 0.05            # guide-wheel rolling resistance on the rail

# ---- linear force from the motors (T = F * r  ->  F = T / r), x n_motors ----
F_stall = n_motors * T_stall_motor / r
F_rated = n_motors * T_rated_motor / r

# ---- load to climb the rail ----
F_gravity = m * g * math.sin(tilt)
F_roll = m * g * mu_roll * math.cos(tilt)
F_load = F_gravity + F_roll

# ---- speeds ----
v_noload = (rpm_noload / 60.0) * math.pi * pinion_d     # m/s at the rack
# pick a drive force ceiling for the controller: rated, with headroom over load
F_drive = F_rated
margin_rated = F_rated / F_load
margin_stall = F_stall / F_load

print(f"Pinion radius r            = {r*1000:.1f} mm")
print(f"Motor stall force (x{n_motors})    = {F_stall:.1f} N")
print(f"Motor rated force (x{n_motors})    = {F_rated:.1f} N   <- controller effort ceiling")
print(f"Load to climb (grav+roll)  = {F_load:.1f} N  (gravity {F_gravity:.1f} + roll {F_roll:.1f})")
print(f"Margin: rated/load         = {margin_rated:.2f}x   stall/load = {margin_stall:.2f}x")
print(f"No-load rail speed         = {v_noload*1000:.0f} mm/s ({v_noload:.3f} m/s)")
print()
print(f"=> A rack-and-pinion driven by the two GA25-370s delivers {F_rated:.0f} N "
      f"rated\n   ({F_stall:.0f} N stall) against a {F_load:.0f} N climbing load: it "
      f"climbs with\n   {margin_rated:.1f}x margin at rated torque. Friction wheels "
      f"could not, because\n   wheel-glass traction (mu*N) capped the usable force; the "
      f"geared mesh does not.")
print(f"\nSim settings: prismatic effort limit = {F_rated:.0f} N, target speed "
      f"= 0.08 m/s.")
