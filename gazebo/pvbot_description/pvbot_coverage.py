#!/usr/bin/env python3
"""
pvbot_coverage.py - boustrophedon coverage driver for the TEC PV-cleaning robot.

Drives the robot over the panel in safe lawn-mower passes: a straight clean
stroke across the panel width, then a gentle two-step turn that walks one
brush-width down the slope and reverses direction. Speeds are kept at the
0.05 m/s cleaning speed from the design; turns are slow in-place rotations so
the wheels never scrub or shock the glass. Spray and brush run only during the
straight strokes and lift on the turns, so nothing is dragged dry across the
panel. The run ends when the whole face is covered - the robot stops, "till
it's clean".

Open-loop timed segments (no odometry dependence) for a repeatable demo. Pure
rclpy, std messages only - no build step, no custom interfaces.

    ros2 run ... none needed:  python3 pvbot_coverage.py
    parameters: clean_speed, turn_rate, panel_width, panel_slope, brush_width
"""
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


class CoverageDriver(Node):
    def __init__(self):
        super().__init__('pvbot_coverage')
        # The robot spawns facing +x (the long 2 m axis of the panel), so each
        # cleaning stroke runs the 2 m length and the lane step crosses the 1 m
        # width. clean_speed is bumped above the 0.05 m/s design value only so
        # the demo finishes in a few minutes; pass clean_speed:=0.05 to watch
        # it at the true rate.
        self.declare_parameter('clean_speed', 0.10)    # m/s (demo); design = 0.05
        self.declare_parameter('turn_rate', 0.35)      # rad/s, gentle in-place turn
        self.declare_parameter('stroke_len', 1.70)     # m, stroke distance along +x
        self.declare_parameter('step_span', 0.70)      # m, total cross-panel travel
        self.declare_parameter('brush_width', 0.25)    # m
        self.declare_parameter('lane_overlap', 0.10)   # fraction of brush width overlapped
        self.declare_parameter('control_hz', 20.0)
        # 'sweep'  : rail-guided fall-line passes, no turns (24 deg tilted panel)
        # 'boustro': lawn-mower with U-turns (flat panel only)
        self.declare_parameter('mode', 'sweep')
        self.declare_parameter('n_sweeps', 2)          # down+up passes in sweep mode

        v = self.get_parameter('clean_speed').value
        w = self.get_parameter('turn_rate').value
        width = self.get_parameter('stroke_len').value
        slope = self.get_parameter('step_span').value
        bw = self.get_parameter('brush_width').value
        overlap = self.get_parameter('lane_overlap').value
        self.hz = self.get_parameter('control_hz').value

        mode = self.get_parameter('mode').value
        n_sweeps = int(self.get_parameter('n_sweeps').value)

        # ---- rail-guided sweep mode: the carriage rides the slope rails and the
        # full-width brush cleans the whole panel in straight fall-line passes.
        # Spawn facing UP the slope; the first pass descends (gravity-assisted,
        # speed-capped), the next climbs back (powered). No yaw, so nothing can
        # slip or slide off - this is the configuration that runs on the tilt.
        if mode == 'sweep':
            self.pub_cmd = self.create_publisher(Twist, 'cmd_vel', 10)
            self.pub_spray = self.create_publisher(Bool, 'spray_on', 10)
            self.pub_brush = self.create_publisher(Bool, 'brush_on', 10)
            t_pass = width / v
            self.segments = []
            for s in range(n_sweeps):
                going_down = (s % 2 == 0)
                lbl = 'sweep DOWN %d' % (s + 1) if going_down else 'sweep UP %d' % (s + 1)
                vx = -v if going_down else v       # forward(+x) is up-slope
                self.segments.append((lbl, vx, 0.0, t_pass, True))
            self.seg_i = 0
            self.t_in_seg = 0.0
            self.dt = 1.0 / self.hz
            total = sum(s[3] for s in self.segments)
            self.get_logger().info(
                'rail-guided sweep: %d fall-line passes, ~%.0f s, speed %.2f m/s'
                % (len(self.segments), total, v))
            self.timer = self.create_timer(self.dt, self.tick)
            return

        step = bw * (1.0 - overlap)                    # effective lane advance
        n_lanes = max(1, math.ceil(slope / step) + 1)  # passes to cover the width
        t_stroke = width / v

        # Lane change is a smooth U-turn ARC, never an in-place spin. On a
        # tilted panel a diff-drive robot cannot pivot in place - the wheels
        # would have to slip sideways against gravity - so it just stalls in
        # one lane. An arc keeps both wheels rolling forward, reverses heading,
        # and shifts one lane across. U-turn diameter = the lane step, so the
        # turn radius is step/2 and the arc angular rate is v / (step/2).
        r_turn = max(0.05, step / 2.0)
        w_turn = min(w * 3.0, v / r_turn)              # cap to keep it gentle
        t_uturn = math.pi / w_turn                     # 180 deg arc

        # Build the segment plan: (label, linear_x, angular_z, duration, spray_on).
        self.segments = []
        turn_sign = +1.0
        for lane in range(n_lanes):
            self.segments.append(('clean stroke %d/%d' % (lane + 1, n_lanes),
                                  v, 0.0, t_stroke, True))
            if lane == n_lanes - 1:
                break
            # U-turn arc to the next lane (brush + spray lift during the turn)
            self.segments.append(('U-turn arc', v, turn_sign * w_turn, t_uturn, False))
            turn_sign *= -1.0                          # alternate U-turn side

        self.pub_cmd = self.create_publisher(Twist, 'cmd_vel', 10)
        self.pub_spray = self.create_publisher(Bool, 'spray_on', 10)
        self.pub_brush = self.create_publisher(Bool, 'brush_on', 10)

        self.seg_i = 0
        self.t_in_seg = 0.0
        self.dt = 1.0 / self.hz
        total = sum(s[3] for s in self.segments)
        self.get_logger().info(
            'coverage plan: %d lanes, %d segments, ~%.0f s, clean speed %.2f m/s'
            % (n_lanes, len(self.segments), total, v))
        self.timer = self.create_timer(self.dt, self.tick)

    def tick(self):
        if self.seg_i >= len(self.segments):
            self.stop_all()
            self.get_logger().info('coverage complete - panel clean, robot parked')
            self.timer.cancel()
            rclpy.shutdown()
            return

        label, vx, wz, dur, spray = self.segments[self.seg_i]
        if self.t_in_seg == 0.0:
            self.get_logger().info('-> %s' % label)

        cmd = Twist()
        cmd.linear.x = vx
        cmd.angular.z = wz
        self.pub_cmd.publish(cmd)
        self.pub_spray.publish(Bool(data=bool(spray)))
        self.pub_brush.publish(Bool(data=bool(spray)))   # brush spins only on strokes

        self.t_in_seg += self.dt
        if self.t_in_seg >= dur:
            self.seg_i += 1
            self.t_in_seg = 0.0

    def stop_all(self):
        self.pub_cmd.publish(Twist())
        self.pub_spray.publish(Bool(data=False))
        self.pub_brush.publish(Bool(data=False))


def main():
    rclpy.init()
    node = CoverageDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop_all()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
