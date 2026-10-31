import os
from glob import glob

from setuptools import setup

package_name = "ros2_basics"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        # package-index marker: lets `ros2 pkg` find the installed package
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        # the manifest
        ("share/" + package_name, ["package.xml"]),
        # launch files and per-node default parameters
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config", "my_publisher_node"), glob("config/my_publisher_node/*.yaml")),
        (os.path.join("share", package_name, "config", "my_subscriber_node"), glob("config/my_subscriber_node/*.yaml")),
        (os.path.join("share", package_name, "config", "drive_node"), glob("config/drive_node/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="YOUR_FULL_NAME",
    maintainer_email="YOUR_EMAIL@EXAMPLE.COM",
    description="My first ROS 2 package in Duckietown: a publisher, a subscriber and a node that drives the Duckiebot.",
    license="Duckietown License 2.0",
    entry_points={
        "console_scripts": [
            # executable name = python module : function
            "my_publisher_node = ros2_basics.my_publisher_node:main",
            "my_subscriber_node = ros2_basics.my_subscriber_node:main",
            "drive_node = ros2_basics.drive_node:main",
        ],
    },
)
