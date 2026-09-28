"""Forward RViz pose goals to the Nav2 NavigateToPose action."""

from __future__ import annotations

from typing import Sequence

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class RvizBridge(Node):
    """Submit RViz ``goal_pose`` messages to the local Nav2 navigator."""

    def __init__(self) -> None:
        super().__init__("rviz_bridge")
        self._action_client = ActionClient(
            self,
            NavigateToPose,
            "navigate_to_pose",
        )
        self._goal_handle = None
        self._goal_subscription = self.create_subscription(
            PoseStamped,
            "/goal_pose",
            self._on_goal,
            1,
        )

    def _on_goal(self, pose: PoseStamped) -> None:
        if not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning("navigate_to_pose action is unavailable")
            return
        goal = NavigateToPose.Goal()
        goal.pose = pose
        future = self._action_client.send_goal_async(goal)
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future) -> None:
        self._goal_handle = future.result()
        if not self._goal_handle.accepted:
            self.get_logger().warning("RViz navigation goal was rejected")


def main(args: Sequence[str] | None = None) -> None:
    rclpy.init(args=args)
    node = RvizBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node._goal_handle is not None:
            node._goal_handle.cancel_goal_async()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
