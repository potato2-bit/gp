#!/usr/bin/env python3
"""
awh_water_bus.py -- the live water coupling between the AWH dock and the
PV-cleaning robot, run as a ROS 2 node alongside pvbot_coverage.py.

In the Gazebo demo the coverage driver publishes `spray_on` (std_msgs/Bool)
during each cleaning stroke. This node listens to that topic and closes the
water loop the rest of the project only computed on paper:

  * a compressed "sim clock" advances ~one climate day per `day_seconds`;
    each new day the AWH dock adds that day's harvest (sized silica bed x the
    site's climate-driven yield) to the dock reservoir;
  * while `spray_on` is true the carriage tank drains at the spray rate;
  * when the tank drops below a threshold the robot tops it up from the dock
    reservoir (the between-pass refill);
  * if the dock runs dry on a due spray, the event is logged as a deficit --
    the same deferred-clean the annual co-sim counts.

It publishes the live levels and prints a running water balance, so the
integration is observable in the ROS graph, not just in a CSV. The bookkeeping
lives in a plain `WaterBus` class with no ROS dependency, so it is unit-tested
off-board (see test_water_bus.py); the node is a thin wrapper.

Run (in the WSL ROS 2 session, after the world + coverage driver are up):
    python3 awh_water_bus.py --ros-args -p site:=nac -p gel_kg:=45 \
        -p day_seconds:=3.0 -p spray_rate_Lps:=0.05
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")


# ---------------------------------------------------------------------------
# Pure-Python core (no ROS) -- the water accounting
# ---------------------------------------------------------------------------
class WaterBus:
    """Daily AWH harvest + per-tick cleaning draw on a shared dock reservoir
    and a carriage tank. All volumes in litres, time in seconds."""

    def __init__(self, site="nac", gel_kg=45.0, area_m2=46.0, L_per_m2=0.3,
                 spray_rate_Lps=0.05, tank_cap_L=3.6, dock_cap_L=25.0,
                 tank_refill_at=0.25, results_dir=RES):
        self.site = site
        self.gel_kg = float(gel_kg)
        self.area_m2 = float(area_m2)
        self.event_L = L_per_m2 * area_m2
        self.spray_rate = float(spray_rate_Lps)
        self.tank_cap = float(tank_cap_L)
        self.dock_cap = float(dock_cap_L)
        self.tank_refill_at = float(tank_refill_at)

        self.shape, self.per_kg = self._load_yield(results_dir, site)
        self.n_days = len(self.shape)

        # state
        self.day = 0
        self.dock_L = min(self.dock_cap, self.daily_supply(0))
        self.tank_L = self.tank_cap
        # ledger
        self.harvested_L = 0.0
        self.sprayed_L = 0.0
        self.refilled_L = 0.0
        self.deficit_L = 0.0
        self.spray_starved_s = 0.0

    @staticmethod
    def _load_yield(results_dir, site):
        shape = []
        with open(os.path.join(results_dir, "site_yield_shape.csv")) as f:
            for row in csv.DictReader(f):
                shape.append(float(row[site]))
        with open(os.path.join(results_dir, "site_yield_per_kg.json")) as f:
            per_kg = json.load(f)[site]
        return shape, per_kg

    def daily_supply(self, day):
        """Litres the sized bed harvests on this climate day."""
        return self.gel_kg * self.per_kg * self.shape[day % self.n_days]

    # -- events ------------------------------------------------------------
    def advance_day(self):
        """Roll the sim clock one climate day: bank that day's harvest."""
        add = self.daily_supply(self.day)
        room = self.dock_cap - self.dock_L
        self.dock_L += min(add, room)
        self.harvested_L += add
        self.day += 1
        return add

    def spray_tick(self, dt):
        """Spend `dt` seconds of spraying: drain the tank, refilling it from the
        dock when low. Returns litres actually sprayed this tick (short of the
        demand if both stores are dry)."""
        want = self.spray_rate * dt
        got = min(want, self.tank_L)
        self.tank_L -= got
        self.sprayed_L += got
        if got < want:
            self.spray_starved_s += dt * (1 - got / want) if want else 0.0
            self.deficit_L += (want - got)
        # top up the carriage tank from the dock when it runs low
        if self.tank_L < self.tank_refill_at * self.tank_cap:
            need = self.tank_cap - self.tank_L
            pull = min(need, self.dock_L)
            self.tank_L += pull
            self.dock_L -= pull
            self.refilled_L += pull
        return got

    def balance(self):
        return {
            "site": self.site, "sim_day": self.day,
            "dock_L": round(self.dock_L, 2), "tank_L": round(self.tank_L, 2),
            "harvested_L": round(self.harvested_L, 1),
            "sprayed_L": round(self.sprayed_L, 1),
            "refilled_L": round(self.refilled_L, 1),
            "deficit_L": round(self.deficit_L, 2),
            "self_supply_f": round(
                self.harvested_L / self.sprayed_L, 3) if self.sprayed_L else None,
        }


# ---------------------------------------------------------------------------
# ROS 2 wrapper -- imported lazily so this file loads for testing without ROS
# ---------------------------------------------------------------------------
def main():
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Bool, Float32

    class WaterBusNode(Node):
        def __init__(self):
            super().__init__("awh_water_bus")
            self.declare_parameter("site", "nac")
            self.declare_parameter("gel_kg", 45.0)
            self.declare_parameter("area_m2", 46.0)
            self.declare_parameter("spray_rate_Lps", 0.05)
            self.declare_parameter("day_seconds", 3.0)   # wall-s per climate day
            self.declare_parameter("dock_cap_L", 25.0)
            gp = self.get_parameter
            self.bus = WaterBus(
                site=gp("site").value, gel_kg=gp("gel_kg").value,
                area_m2=gp("area_m2").value,
                spray_rate_Lps=gp("spray_rate_Lps").value,
                dock_cap_L=gp("dock_cap_L").value)
            self.day_seconds = float(gp("day_seconds").value)

            self.spray_on = False
            self.sub = self.create_subscription(
                Bool, "spray_on", self._on_spray, 10)
            self.pub_tank = self.create_publisher(Float32, "awh/tank_level", 10)
            self.pub_dock = self.create_publisher(Float32, "awh/dock_reservoir", 10)
            self.pub_f = self.create_publisher(Float32, "awh/self_supply", 10)

            self.dt = 0.1
            self._day_accum = 0.0
            self.create_timer(self.dt, self._tick)
            self.create_timer(2.0, self._report)
            self.get_logger().info(
                f"water bus up: site={self.bus.site} gel={self.bus.gel_kg:.0f} kg "
                f"event={self.bus.event_L:.1f} L, 1 climate day / "
                f"{self.day_seconds:.1f} s")

        def _on_spray(self, msg):
            self.spray_on = bool(msg.data)

        def _tick(self):
            # advance the compressed climate clock
            self._day_accum += self.dt
            if self._day_accum >= self.day_seconds:
                self._day_accum -= self.day_seconds
                add = self.bus.advance_day()
                self.get_logger().info(
                    f"day {self.bus.day}: +{add:.2f} L harvest -> "
                    f"dock {self.bus.dock_L:.1f} L")
            if self.spray_on:
                self.bus.spray_tick(self.dt)
            self.pub_tank.publish(Float32(data=float(self.bus.tank_L)))
            self.pub_dock.publish(Float32(data=float(self.bus.dock_L)))
            b = self.bus.balance()
            if b["self_supply_f"] is not None:
                self.pub_f.publish(Float32(data=float(b["self_supply_f"])))

        def _report(self):
            b = self.bus.balance()
            self.get_logger().info(
                f"tank {b['tank_L']:.2f} | dock {b['dock_L']:.1f} | "
                f"sprayed {b['sprayed_L']:.1f} | harvested {b['harvested_L']:.1f}"
                f" | deficit {b['deficit_L']:.2f} L | f={b['self_supply_f']}")

    rclpy.init()
    node = WaterBusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        import json as _json
        node.get_logger().info("FINAL BALANCE " + _json.dumps(node.bus.balance()))
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
