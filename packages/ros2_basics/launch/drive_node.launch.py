import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    # the robot name is a launch argument; it defaults to the VEHICLE_NAME environment variable
    veh = LaunchConfiguration("veh")
    car_cmd_topic = LaunchConfiguration("car_cmd_topic")
    # default parameters of the node, installed by setup.py under share/ros2_basics/config/
    config = os.path.join(get_package_share_directory("ros2_basics"), "config", "drive_node", "default.yaml")
    return LaunchDescription([
        DeclareLaunchArgument("veh", default_value=EnvironmentVariable("VEHICLE_NAME"),
                              description="robot name (namespace of every topic)"),
        # The kinematics_node of the robot's core stack listens on `car_cmd_switch_node/cmd` (current `ente`
        # source); robot images built before 2026-10-20 listen on `car_cmd`: pass `car_cmd_topic:=car_cmd` for those.
        DeclareLaunchArgument("car_cmd_topic",
                              default_value=EnvironmentVariable("CAR_CMD_TOPIC", default_value="car_cmd_switch_node/cmd"),
                              description="topic (relative to the robot namespace) the kinematics node reads car commands from"),
        Node(
            package="ros2_basics",
            executable="drive_node",
            name="drive_node",
            namespace=veh,
            parameters=[config],
            # remapping: the name used in the code -> the name used on this robot
            remappings=[("car_cmd_switch_node/cmd", car_cmd_topic)],
            output="screen",
            emulate_tty=True,
        ),
    ])
