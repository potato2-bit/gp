#!/usr/bin/env python3
"""
pvbot_rail_drive.py - smooth kinematic rack-and-pinion drive for the gantry.

A free-wheel model cannot climb 24 deg glass (the wheels slip). The real drive
is a rack-and-pinion: positive, geared, constrained to the rail, so the carriage
moves DOWN and UP without slipping. This node reproduces that by setting the
carriage pose along the rail at 30 Hz through /gazebo/set_entity_state, with the
velocity zeroed each step so gravity cannot drift it. The result is a smooth
glide down the rail (cleaning) and back up (return), looping.

Run after the carriage is spawned:  python3 pvbot_rail_drive.py
The world must load libgazebo_ros_state.so (panel_world_tilt.sdf does).
"""
import math
import rclpy
from rclpy.node import Node
from gazebo_msgs.srv import SetEntityState
from gazebo_msgs.msg import EntityState
from geometry_msgs.msg import Pose, Point, Quaternion, Twist

# rail line in world coords (measured from the physics run)
TOP = (0.65, 0.91)      # x, z at the top of the slope
BOT = (-0.72, 0.28)     # x, z at the bottom
PITCH = -0.41888        # 24 deg, carriage sits flat on the glass
QY = math.sin(PITCH / 2.0)
QW = math.cos(PITCH / 2.0)


class RailDrive(Node):
    def __init__(self):
        super().__init__('pvbot_rail_drive')
        self.declare_parameter('hz', 30.0)
        self.declare_parameter('speed', 0.40)   # rail-fractions per second
        self.declare_parameter('dwell', 0.4)    # pause at each end (s)
        self.hz = self.get_parameter('hz').value
        self.speed = self.get_parameter('speed').value
        self.dwell = self.get_parameter('dwell').value

        self.cli = self.create_client(SetEntityState, '/gazebo/set_entity_state')
        if not self.cli.wait_for_service(timeout_sec=15.0):
            self.get_logger().error('/gazebo/set_entity_state not available - '
                                     'is libgazebo_ros_state.so loaded?')
            raise SystemExit(1)
        self.get_logger().info('rack-and-pinion rail drive: gliding down and up.')

        self.t = 0.0          # 0 = top, 1 = bottom
        self.direction = 1
        self.pause = 0.0
        self.timer = self.create_timer(1.0 / self.hz, self.tick)

    def place(self, frac):
        x = TOP[0] + (BOT[0] - TOP[0]) * frac
        z = TOP[1] + (BOT[1] - TOP[1]) * frac
        st = EntityState()
        st.name = 'pvbot'
        st.pose = Pose(position=Point(x=x, y=0.0, z=z),
                       orientation=Quaternion(x=0.0, y=QY, z=0.0, w=QW))
        st.twist = Twist()          # zero velocity - no gravity drift
        st.reference_frame = 'world'
        req = SetEntityState.Request()
        req.state = st
        self.cli.call_async(req)

    def tick(self):
        if self.pause > 0.0:
            self.pause -= 1.0 / self.hz
            self.place(self.t)
            return
        self.t += self.direction * self.speed / self.hz
        if self.t >= 1.0:
            self.t = 1.0
            self.direction = -1
            self.pause = self.dwell
        elif self.t <= 0.0:
            self.t = 0.0
            self.direction = 1
            self.pause = self.dwell
        self.place(self.t)


def main():
    rclpy.init()
    node = RailDrive()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
