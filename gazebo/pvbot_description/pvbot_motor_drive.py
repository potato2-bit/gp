#!/usr/bin/env python3
"""
pvbot_motor_drive.py - velocity loop for the rack-and-pinion thrust.

Models the real drive: two GA25-370 (1:71) motors -> Ø30 mm pinions -> a linear
thrust on the carriage, capped at the 45 N rated ceiling from
scripts/rack_pinion_drive.py. A PI-ish velocity loop (P + gravity feed-forward)
sets the thrust each step and applies it through libgazebo_ros_force, so the
carriage climbs the 24 deg rail under real force (35.5 N load < 45 N drive). It
sweeps down (cleaning) then up (return) and loops.

  ros2 run ... none needed:  python3 pvbot_motor_drive.py
Requires pvbot_railed.urdf (force + p3d odom plugins).
"""
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Wrench

# rail geometry (world): bottom and up-slope unit vector
BOT = (-0.72, 0.28)
SLOPE = (math.cos(math.radians(24.0)), math.sin(math.radians(24.0)))  # (0.914, 0.407)

# drivetrain ceiling and load (scripts/rack_pinion_drive.py)
F_MAX = 45.0           # N, two GA25-370 rated thrust
MASS = 5.93            # kg, carriage (URDF sum)
G = 9.81
F_GRAV = MASS * G * math.sin(math.radians(24.0))   # 23.7 N, gravity along slope


class MotorDrive(Node):
    def __init__(self):
        super().__init__('pvbot_motor_drive')
        self.declare_parameter('v_clean', 0.10)    # m/s the setpoint glides along the rail
        self.declare_parameter('kp', 300.0)        # N/m, position stiffness
        self.declare_parameter('kd', 120.0)        # N.s/m, velocity damping (overdamped)
        self.declare_parameter('s_lo', 0.15)       # bottom of travel (m up the rail)
        self.declare_parameter('s_hi', 1.40)       # top of travel
        self.dt = 0.02
        self.v_clean = self.get_parameter('v_clean').value
        self.kp = self.get_parameter('kp').value
        self.kd = self.get_parameter('kd').value
        self.s_lo = self.get_parameter('s_lo').value
        self.s_hi = self.get_parameter('s_hi').value

        self.s = self.s_hi          # measured position along the rail
        self.v = 0.0
        self.s_sp = None            # moving setpoint - latched to the first odom
        self.direction = -1         # setpoint descends first
        self.pub = self.create_publisher(Wrench, '/pvbot/gazebo_ros_force', 10)
        self.create_subscription(Odometry, '/pvbot/odom', self.odom_cb, 10)
        self.timer = self.create_timer(self.dt, self.tick)   # 50 Hz
        self.get_logger().info(
            'rack-and-pinion PD drive: F_max=%.0f N vs load %.1f N -> climbs.'
            % (F_MAX, F_GRAV + 3.6))

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        v = msg.twist.twist.linear
        self.s = (p.x - BOT[0]) * SLOPE[0] + (p.z - BOT[1]) * SLOPE[1]
        self.v = v.x * SLOPE[0] + v.z * SLOPE[1]      # velocity along the rail

    def tick(self):
        if self.s_sp is None:           # latch the setpoint to where it spawned
            self.s_sp = self.s
        # glide the setpoint smoothly along the rail, reversing at the ends
        self.s_sp += self.direction * self.v_clean * self.dt
        if self.s_sp <= self.s_lo:
            self.s_sp = self.s_lo
            self.direction = +1
        elif self.s_sp >= self.s_hi:
            self.s_sp = self.s_hi
            self.direction = -1
        v_sp = self.direction * self.v_clean
        # gravity feed-forward + position-PD tracking the moving setpoint
        f = F_GRAV + self.kp * (self.s_sp - self.s) + self.kd * (v_sp - self.v)
        f = max(-F_MAX, min(F_MAX, f))
        # apply the thrust along the fixed WORLD up-slope direction, so body
        # pitch cannot redirect it (that was the instability)
        w = Wrench()
        w.force.x = float(f * SLOPE[0])
        w.force.z = float(f * SLOPE[1])
        self.pub.publish(w)


def main():
    rclpy.init()
    node = MotorDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
