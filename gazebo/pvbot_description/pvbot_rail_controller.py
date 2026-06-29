#!/usr/bin/env python3
"""
pvbot_rail_controller.py - sweep command for the effort-limited rail drive.

Reads the rail position from /joint_states and commands the velocity controller
(velocity_controllers/JointGroupVelocityController) to glide the carriage down
the rail (cleaning) then back up (return), reversing at the ends. The prismatic
joint is a hard constraint and its effort is capped at the 45 N motor ceiling in
pvbot_railed_control.urdf, so the motion is smooth AND the climb is real (45 N >
35.5 N load). Publishes to /rail_velocity_controller/commands.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


class RailController(Node):
    def __init__(self):
        super().__init__('pvbot_rail_controller')
        self.declare_parameter('v_clean', 0.09)   # m/s along the rail (motor speed)
        self.declare_parameter('s_lo', 0.20)       # reverse with margin from the 0.0 stop
        self.declare_parameter('s_hi', 1.20)       # and from the 1.40 stop
        self.v_clean = self.get_parameter('v_clean').value
        self.s_lo = self.get_parameter('s_lo').value
        self.s_hi = self.get_parameter('s_hi').value

        self.pos = None
        self.direction = -1                        # descend first
        self.pub = self.create_publisher(Float64MultiArray, '/rail_velocity_controller/commands', 10)
        self.create_subscription(JointState, '/joint_states', self.js_cb, 10)
        self.timer = self.create_timer(0.05, self.tick)   # 20 Hz
        self.get_logger().info('rail controller: effort-limited velocity sweep (down/up).')

    def js_cb(self, msg):
        if 'rail_slide' in msg.name:
            self.pos = msg.position[msg.name.index('rail_slide')]

    def tick(self):
        if self.pos is None:
            return
        if self.pos <= self.s_lo and self.direction < 0:
            self.direction = +1
        elif self.pos >= self.s_hi and self.direction > 0:
            self.direction = -1
        cmd = Float64MultiArray()
        cmd.data = [self.direction * self.v_clean]
        self.pub.publish(cmd)


def main():
    rclpy.init()
    node = RailController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.pub.publish(Float64MultiArray(data=[0.0]))
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
