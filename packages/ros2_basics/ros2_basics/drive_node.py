#!/usr/bin/env python3
"""Drive the Duckiebot from a ROS 2 node.

The node publishes `duckietown_msgs/msg/Twist2DStamped` commands (a forward speed `v` in m/s and
an angular speed `omega` in rad/s) on `car_cmd_switch_node/cmd`. The `kinematics_node` of the
Duckiebot's ROS 2 stack turns them into wheel commands.

- `v`, `omega`, `rate_hz`, `max_duration` are parameters: change them live with `ros2 param set`
  or with a `ParamPanel` in the notebooks;
- `~/start` and `~/stop` are `std_srvs/srv/Trigger` services: call them with
  `ros2 service call /ROBOT/drive_node/start std_srvs/srv/Trigger` or with `ActionButtons`.

Topic names are RELATIVE: the launch file puts the node in the robot namespace (`/ROBOT`).
"""
import rclpy
from duckietown_msgs.msg import Twist2DStamped
from rclpy.node import Node
from std_srvs.srv import Trigger

from lx_ros2_tools.params import LiveParams
from lx_ros2_tools.robot import get_wheel_params


class DriveNode(Node):
    def __init__(self) -> None:
        super().__init__("drive_node")
        # robot name = namespace given by the launch file (e.g. "/myrobot" -> "myrobot")
        self.veh = self.get_namespace().strip("/")

        # parameters (defaults also in config/drive_node/default.yaml, loaded by the launch file)
        self.params = LiveParams(
            self,
            {"v": 0.2, "omega": 0.0, "rate_hz": 10.0, "max_duration": 5.0, "enabled": False},
            on_change=self._on_param,
        )

        # physical parameters of this robot (calibration file on the robot, built-in defaults otherwise)
        self.wheels = get_wheel_params(self.veh)
        self.get_logger().info(f"robot '{self.veh}': wheel baseline {self.wheels.baseline} m, "
                               f"radius {self.wheels.radius} m ({self.wheels.source})")

        # publisher: car commands for the kinematics node of the robot
        self.pub_cmd = self.create_publisher(Twist2DStamped, "car_cmd_switch_node/cmd", 10)

        # services driven from the terminal or from the notebook panels (ActionButtons)
        self.create_service(Trigger, "~/start", self.srv_start)
        self.create_service(Trigger, "~/stop", self.srv_stop)

        # control loop
        self._started_at = None
        self._timer = self.create_timer(1.0 / self.params.rate_hz, self.loop)
        self.get_logger().info(f"ready: publishing on '{self.pub_cmd.topic_name}' once started")

    # --- callbacks ------------------------------------------------------------------------------
    def _on_param(self, name, value) -> None:
        if name == "rate_hz" and value > 0:
            self.destroy_timer(self._timer)
            self._timer = self.create_timer(1.0 / value, self.loop)
        self.get_logger().info(f"parameter {name} = {value}")

    def loop(self) -> None:
        """Called `rate_hz` times per second; publishes one command while driving is enabled."""
        if not self.params.enabled:
            return
        now = self.get_clock().now()
        elapsed = (now - self._started_at).nanoseconds * 1e-9 if self._started_at is not None else 0.0
        if self.params.max_duration > 0 and elapsed > self.params.max_duration:
            self.get_logger().info(f"max_duration ({self.params.max_duration} s) reached: stopping")
            self.stop()
            return

        cmd = Twist2DStamped()
        cmd.header.stamp = now.to_msg()
        # ---------------------------------------------------------------------------------------
        # YOUR CODE BELOW THIS LINE: decide the command to send at time `elapsed`
        cmd.v = float(self.params.v)
        cmd.omega = float(self.params.omega)
        # YOUR CODE ABOVE THIS LINE
        # ---------------------------------------------------------------------------------------
        self.pub_cmd.publish(cmd)

    def stop(self) -> None:
        """Disable driving and send one zero command so the wheels stop immediately."""
        self.params.enabled = False
        self._started_at = None
        stop = Twist2DStamped()
        stop.header.stamp = self.get_clock().now().to_msg()
        self.pub_cmd.publish(stop)

    # --- services -------------------------------------------------------------------------------
    def srv_start(self, _request, response):
        self._started_at = self.get_clock().now()
        self.params.enabled = True
        response.success = True
        response.message = f"driving with v={self.params.v} m/s, omega={self.params.omega} rad/s"
        self.get_logger().info(response.message)
        return response

    def srv_stop(self, _request, response):
        self.stop()
        response.success = True
        response.message = "stopped"
        self.get_logger().info(response.message)
        return response


def main(args=None):
    rclpy.init(args=args)
    node = DriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
