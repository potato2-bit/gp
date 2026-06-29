#!/usr/bin/env python3
"""Read rail_slide position for ~24 s and print the trajectory (rclpy, not ros2cli).
Used by test_launch.sh to prove the effort-limited drive sweeps down and up."""
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class Mon(Node):
    def __init__(self):
        super().__init__('mon')
        self.samples = []
        self.t0 = time.time()
        self.create_subscription(JointState, '/joint_states', self.cb, 50)

    def cb(self, m):
        if 'rail_slide' in m.name:
            self.samples.append((round(time.time() - self.t0, 1),
                                 round(m.position[m.name.index('rail_slide')], 3)))


def main():
    rclpy.init()
    n = Mon()
    end = time.time() + 24
    while time.time() < end and rclpy.ok():
        rclpy.spin_once(n, timeout_sec=0.2)
    s = n.samples
    if not s:
        print("NO joint_states received")
    else:
        pos = [p for _, p in s]
        print("samples=%d  min=%.3f  max=%.3f  range=%.3f" %
              (len(s), min(pos), max(pos), max(pos) - min(pos)))
        last = -9
        for t, p in s:
            if t - last >= 2.0:
                print("  t=%4.1f  rail=%.3f" % (t, p)); last = t
    rclpy.shutdown()


if __name__ == '__main__':
    main()
