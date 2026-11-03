#!/usr/bin/env python3
"""A minimal ROS 2 publisher.

A timer fires `rate_hz` times per second; every time it does, the callback fills a
`std_msgs/msg/String` message and publishes it on the topic `chatter`.

Both the text and the rate are ROS 2 *parameters*: their defaults live in
`config/my_publisher_node/default.yaml` and they can be changed while the node runs with
`ros2 param set <node> message "..."` or from a notebook panel.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lx_ros2_tools.params import LiveParams

NODE_NAME = "my_publisher_node"
# relative name: in the root namespace it resolves to `/chatter`, under a robot namespace to `/ROBOT/chatter`
TOPIC_NAME = "chatter"
# how many outgoing messages are kept while subscribers catch up (the QoS history depth)
QUEUE_DEPTH = 10


class MyPublisherNode(Node):
    """Publish a text message periodically on the configured topic."""

    def __init__(self) -> None:
        # the Node superclass gives this object a name in the ROS 2 graph and the graph APIs
        super().__init__(NODE_NAME)

        # parameters (defaults also in config/my_publisher_node/default.yaml, loaded by the launch file)
        self.params = LiveParams(self, {"message": "Hello from ROS 2!", "rate_hz": 1.0}, on_change=self._on_param)

        # the message type, topic name and queue depth define this publisher
        self._publisher = self.create_publisher(String, TOPIC_NAME, QUEUE_DEPTH)

        # timers use seconds, so convert the publication rate from hertz first
        self._count = 0
        self._timer = self.create_timer(1.0 / self.params.rate_hz, self._publish_message)
        self.get_logger().info(f"publishing on '{self._publisher.topic_name}' at {self.params.rate_hz} Hz")

    # --- callbacks ------------------------------------------------------------------------------
    def _on_param(self, name: str, value) -> None:
        """Called by LiveParams after a parameter was changed (e.g. with `ros2 param set`)."""
        if name == "rate_hz":
            if value <= 0:
                self.get_logger().warning("rate_hz must be positive, keeping the previous timer")
                return
            # replace the timer so the new rate takes effect immediately
            self.destroy_timer(self._timer)
            self._timer = self.create_timer(1.0 / value, self._publish_message)
        self.get_logger().info(f"parameter {name} = {value!r}")

    def _publish_message(self) -> None:
        """Create, log and publish one message (invoked by the timer)."""
        msg = String()
        msg.data = f"{self.params.message} [{self._count}]"
        self._count += 1
        # the log shows what the node sends; `publish` hands the message to the middleware
        self.get_logger().info(f'publishing: "{msg.data}"')
        self._publisher.publish(msg)


def main(args=None):
    # initialize the ROS 2 client library before creating any node
    rclpy.init(args=args)
    node = MyPublisherNode()
    try:
        # process timer (and other) callbacks until Ctrl-C
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
