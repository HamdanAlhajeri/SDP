from setuptools import find_packages, setup

package_name = 'detection_and_avoidance'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/avoidance.launch.py']),
        ('share/' + package_name + '/config', ['config/avoidance.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='SDP Team',
    maintainer_email='maintainer@example.com',
    description='Reactive Hokuyo lidar obstacle avoidance with VESC control.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'avoid_obstacles = detection_and_avoidance.avoid_obstacles:main',
        ],
    },
)
