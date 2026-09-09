#!/usr/bin/env bash
# Build and run the ROS 2 lidar avoidance node on the Jetson.

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
BUILD_PACKAGE=true
RESTART_TELEOP=false

usage() {
    echo "Usage: $0 [--no-build]"
    echo "  --no-build  Launch the previously built package immediately."
}

if [[ ${1:-} == "--no-build" ]]; then
    BUILD_PACKAGE=false
elif [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
    usage
    exit 0
elif [[ $# -gt 0 ]]; then
    usage >&2
    exit 2
fi

# ROS_DISTRO is normally set after sourcing ROS. Use Humble as the Jetson
# default, while still allowing: ROS_DISTRO=jazzy ./run_avoidance.sh
ROS_VERSION="${ROS_DISTRO:-humble}"
ROS_SETUP="/opt/ros/${ROS_VERSION}/setup.bash"

if [[ ! -f "${ROS_SETUP}" ]]; then
    echo "ERROR: ROS 2 ${ROS_VERSION} was not found at ${ROS_SETUP}." >&2
    echo "Run with the installed distribution, for example:" >&2
    echo "  ROS_DISTRO=jazzy bash $0" >&2
    exit 1
fi

# Some ROS setup scripts inspect unset variables, so temporarily disable -u.
set +u
source "${ROS_SETUP}"
set -u

if ${BUILD_PACKAGE}; then
    echo "Building detection_and_avoidance in ${WORKSPACE_DIR} ..."
    cd "${WORKSPACE_DIR}"
    colcon build --packages-select detection_and_avoidance --symlink-install
fi

WORKSPACE_SETUP="${WORKSPACE_DIR}/install/setup.bash"
if [[ ! -f "${WORKSPACE_SETUP}" ]]; then
    echo "ERROR: ${WORKSPACE_SETUP} does not exist. Build the workspace first." >&2
    exit 1
fi

set +u
source "${WORKSPACE_SETUP}"
set -u

if [[ ! -e /dev/vesc ]]; then
    echo "ERROR: /dev/vesc does not exist." >&2
    echo "Check the VESC USB cable and udev configuration." >&2
    exit 1
fi

if [[ ! -r /dev/vesc || ! -w /dev/vesc ]]; then
    echo "ERROR: The current user cannot access /dev/vesc." >&2
    echo "Add the user to dialout, then log out and back in:" >&2
    echo "  sudo usermod -aG dialout \$USER" >&2
    exit 1
fi

cleanup() {
    # The ROS node stops the motor and centres steering during shutdown.
    if ${RESTART_TELEOP}; then
        echo "Restarting rc-teleop.service ..."
        sudo systemctl start rc-teleop.service || true
    fi
}
trap cleanup EXIT

if command -v systemctl >/dev/null 2>&1 \
        && systemctl is-active --quiet rc-teleop.service; then
    echo "Stopping rc-teleop.service while avoidance owns the VESC ..."
    sudo systemctl stop rc-teleop.service
    RESTART_TELEOP=true
fi

if ! ros2 topic list 2>/dev/null | grep -Fxq '/scan'; then
    echo "ERROR: No /scan topic was found." >&2
    echo "Start the Hokuyo ROS 2 driver in another terminal, then run this again." >&2
    exit 1
fi

echo "Lidar and VESC detected. Starting obstacle avoidance."
echo "Press Ctrl+C to stop. Keep the wheels raised for the first test."
ros2 launch detection_and_avoidance avoidance.launch.py
