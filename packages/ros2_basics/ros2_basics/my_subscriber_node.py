#!/usr/bin/env python3
"""A ROS 2 subscriber.

The node listens to three kinds of data:

- `chatter` (`std_msgs/msg/String`): the text published by `my_publisher_node`; every message is logged;
- the wheel encoders of the Duckiebot (`duckietown_msgs/msg/WheelEncoderStamped`);
- the camera of the Duckiebot (`sensor_msgs/msg/CompressedImage`).

Sensor streams are subscribed with the *sensor data* QoS profile (best effort, small history):
a sensor stream should always deliver the freshest reading rather than every reading.
The robot topics use RELATIVE names: the launch file puts the node in the robot namespace, so
`camera_node/image/compressed` becomes `/ROBOT/camera_node/image/compressed`.
"""
import rclpy
from duckietown_msgs.msg import WheelEncoderStamped
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

from lx_ros2_tools.image import compressed_to_bgr
from lx_ros2_tools.params import LiveParams

NODE_NAME = "my_subscriber_node"
TOPIC_TO_SUBSCRIBE = "chatter"
QUEUE_DEPTH = 10


class MySubscriberNode(Node):
    """Log messages received on `chatter` and summarize the robot's sensor streams."""

    def __init__(self) -> None:
        super().__init__(NODE_NAME)

        # parameters (defaults also in config/my_subscriber_node/default.yaml)
        self.params = LiveParams(self, {"report_period": 2.0})

        # the callback is passed WITHOUT parentheses: ROS 2 calls it for every incoming message
        self._subscription = self.create_subscription(String, TOPIC_TO_SUBSCRIBE, self._on_chatter, QUEUE_DEPTH)

        # robot sensor streams: sensor-data QoS (best effort) for images and encoder ticks
        self.create_subscription(WheelEncoderStamped, "left_wheel_encoder_driver_node/tick",
                                 self._on_left_tick, qos_profile_sensor_data)
        self.create_subscription(WheelEncoderStamped, "right_wheel_encoder_driver_node/tick",
                                 self._on_right_tick, qos_profile_sensor_data)
        self.create_subscription(CompressedImage, "camera_node/image/compressed",
                                 self._on_image, qos_profile_sensor_data)

        # bookkeeping for the periodic report
        self._ticks = {"left": None, "right": None}
        self._frames = 0
        self._last_image = None
        self.create_timer(float(self.params.report_period), self._report)
        self.get_logger().info(f"listening on '{self._subscription.topic_name}'")

    # --- callbacks ------------------------------------------------------------------------------
    def _on_chatter(self, msg: String) -> None:
        # `data` is the only field of std_msgs/msg/String
        self.get_logger().info(f'I heard: "{msg.data}"')

    def _on_left_tick(self, msg: WheelEncoderStamped) -> None:
        # `data` counts encoder ticks; `resolution` ticks make one wheel revolution
        self._ticks["left"] = (msg.data, msg.resolution)

    def _on_right_tick(self, msg: WheelEncoderStamped) -> None:
        self._ticks["right"] = (msg.data, msg.resolution)

    def _on_image(self, msg: CompressedImage) -> None:
        # keep only the latest frame; decoding happens in the (slow) report, not here
        self._frames += 1
        self._last_image = msg

    def _report(self) -> None:
        """Summarize the robot streams; stays silent while no robot data arrives."""
        if self._frames == 0 and all(t is None for t in self._ticks.values()):
            return
        parts = []
        for side, tick in self._ticks.items():
            if tick is not None:
                parts.append(f"{side} encoder: {tick[0]} ticks ({tick[1]}/rev)")
        if self._last_image is not None:
            h, w = compressed_to_bgr(self._last_image).shape[:2]
            parts.append(f"camera: {self._frames} frames, last {w}x{h} {self._last_image.format}")
        self.get_logger().info(" | ".join(parts))


def main(args=None):
    rclpy.init(args=args)
    node = MySubscriberNode()
    try:
        # process received messages (and the report timer) until Ctrl-C
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
