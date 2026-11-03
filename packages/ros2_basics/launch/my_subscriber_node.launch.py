import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    # the robot name is a launch argument; it defaults to the VEHICLE_NAME environment variable
    veh = LaunchConfiguration("veh")
    # default parameters of the node, installed by setup.py under share/ros2_basics/config/
    config = os.path.join(get_package_share_directory("ros2_basics"), "config", "my_subscriber_node", "default.yaml")
    return LaunchDescription([
        DeclareLaunchArgument("veh", default_value=EnvironmentVariable("VEHICLE_NAME"),
                              description="robot name (namespace of every topic)"),
        Node(
            package="ros2_basics",
            executable="my_subscriber_node",
            name="my_subscriber_node",
            namespace=veh,
            parameters=[config],
            output="screen",
            emulate_tty=True,
        ),
    ])
