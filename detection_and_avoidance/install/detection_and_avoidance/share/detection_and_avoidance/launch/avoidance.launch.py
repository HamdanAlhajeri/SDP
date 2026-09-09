from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import os


def generate_launch_description():
    package_share = get_package_share_directory('detection_and_avoidance')
    config = os.path.join(package_share, 'config', 'avoidance.yaml')
    return LaunchDescription([
        Node(
            package='detection_and_avoidance',
            executable='avoid_obstacles',
            name='avoid_obstacles',
            output='screen',
            parameters=[config],
        ),
    ])
