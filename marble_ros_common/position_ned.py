"""Convert filtered odometry into the MARBLE navigation-status convention."""

from __future__ import annotations

from math import asin, atan2, pi
from typing import Sequence

import rclpy
import tf2_ros
from auv_msgs.msg import NavigationStatus
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node


class PositionNed(Node):
    """Publish navigation status and a map-to-base transform from odometry."""

    def __init__(self) -> None:
        super().__init__("position_ned")
        self._position_publisher = self.create_publisher(
            NavigationStatus,
            "position",
            1,
        )
        self._odometry_subscription = self.create_subscription(
            Odometry,
            "odometry/filtered",
            self._on_odometry,
            1,
        )
        self._transform_broadcaster = tf2_ros.TransformBroadcaster(self)
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("odom_frame", "map")
        self._base_frame = self.get_parameter("base_frame").value
        self._odom_frame = self.get_parameter("odom_frame").value

    def _on_odometry(self, message: Odometry) -> None:
        status = NavigationStatus()
        status.header = message.header
        status.position.north = message.pose.pose.position.y
        status.position.east = message.pose.pose.position.x
        status.position.depth = -message.pose.pose.position.z

        orientation = message.pose.pose.orientation
        roll = atan2(
            2.0 * (orientation.y * orientation.z + orientation.x * orientation.w),
            1.0 - 2.0 * (orientation.x**2 + orientation.y**2),
        )
        pitch_argument = 2.0 * (
            orientation.x * orientation.z - orientation.y * orientation.w
        )
        pitch = -asin(max(-1.0, min(1.0, pitch_argument)))
        yaw = atan2(
            2.0 * (orientation.y * orientation.x + orientation.w * orientation.z),
            1.0 - 2.0 * (orientation.y**2 + orientation.z**2),
        )

        status.orientation.x = roll
        status.orientation.y = pitch
        status.orientation.z = -yaw + pi / 2.0
        if status.orientation.z > pi:
            status.orientation.z -= 2.0 * pi
        elif status.orientation.z <= -pi:
            status.orientation.z += 2.0 * pi

        status.seafloor_velocity.x = message.twist.twist.linear.x
        status.seafloor_velocity.y = -message.twist.twist.linear.y
        status.seafloor_velocity.z = -message.twist.twist.linear.z
        status.orientation_rate.x = message.twist.twist.angular.x
        status.orientation_rate.y = -message.twist.twist.angular.y
        status.orientation_rate.z = -message.twist.twist.angular.z
        self._position_publisher.publish(status)

        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self._odom_frame
        transform.child_frame_id = self._base_frame
        transform.transform.translation.x = message.pose.pose.position.x
        transform.transform.translation.y = message.pose.pose.position.y
        transform.transform.translation.z = message.pose.pose.position.z
        transform.transform.rotation = orientation
        self._transform_broadcaster.sendTransform(transform)


def main(args: Sequence[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PositionNed()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
