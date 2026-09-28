"""Reusable helpers for ROS 2 Python launch files."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    EnvironmentVariable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.descriptions import ParameterFile

from marble_ros_common.yaml_params_resolver import YamlParamsResolver


_CONFIG_PATH_VARIABLE = "ROS_CONFIG_DIR"


class ParamSubstitutor:
    """Create a parameter file that resolves launch substitutions in YAML."""

    def __init__(
        self,
        launch_params: Sequence[Mapping[str, Any]] | None = None,
        param_rewrites: Mapping[str, Any] | None = None,
    ) -> None:
        self._launch_params = launch_params
        self._param_rewrites = param_rewrites

    def perform(self, source_file: Any) -> ParameterFile:
        """Return a launch parameter file backed by the resolved YAML source."""
        return ParameterFile(
            YamlParamsResolver(
                source_file,
                self._launch_params,
                self._param_rewrites,
            )
        )


def LC(name: str) -> LaunchConfiguration:
    """Return a launch configuration that defaults to an empty value."""
    return LaunchConfiguration(name, default="")


def get_common_launch_arguments(node_name: str = "dummy") -> list[dict[str, Any]]:
    """Return launch-argument definitions shared by MARBLE node launchers."""
    return [
        {
            "name": "node_name",
            "default": node_name,
            "description": "Name of the ROS node.",
        },
        {
            "name": "namespace",
            "default": "",
            "description": "Namespace for nodes in this launch file.",
        },
        {
            "name": "namespace_s",
            "default": namespace_slashed_expression(),
            "description": "Namespace with a trailing slash when set.",
        },
        {
            "name": "debug",
            "default": "false",
            "description": "Enable debug mode.",
        },
        {
            "name": "log_level",
            "default": "info",
            "description": "ROS log level.",
        },
    ]


def declare_launch_parameters(
    parameters: Sequence[Mapping[str, Any]],
) -> list[DeclareLaunchArgument]:
    """Convert declarative parameter definitions into launch arguments."""
    return [
        DeclareLaunchArgument(
            parameter["name"],
            default_value=parameter.get("default", ""),
            description=parameter.get("description", ""),
        )
        for parameter in parameters
    ]


def set_configurable_parameters(
    parameters: Sequence[Mapping[str, Any]],
) -> dict[str, LaunchConfiguration]:
    """Map every declared parameter name to its launch configuration."""
    return {
        parameter["name"]: LaunchConfiguration(parameter["name"])
        for parameter in parameters
    }


def namespace_slashed_expression() -> PythonExpression:
    """Return the namespace followed by a slash when a namespace is set."""
    namespace = LaunchConfiguration("namespace")
    return PythonExpression([
        "'", namespace, "' + '/' if '", namespace, "' else ''",
    ])


def add_namespace_if_exists(
    namespace: LaunchConfiguration,
    name: str,
) -> PythonExpression:
    """Prefix a frame or topic name with the configured namespace."""
    return PythonExpression([
        "'", namespace, "' + '/' + '", name, "' if '", namespace,
        "' else '", name, "'",
    ])


def resolve_conf_file(file_name: str, default_directory: str) -> PathJoinSubstitution:
    """Resolve a configurable file from ROS_CONFIG_DIR or a package default."""
    configured_directory = os.environ.get(_CONFIG_PATH_VARIABLE)
    if configured_directory and os.path.isfile(
        os.path.join(configured_directory, file_name)
    ):
        return PathJoinSubstitution([
            EnvironmentVariable(_CONFIG_PATH_VARIABLE),
            file_name,
        ])
    return PathJoinSubstitution([default_directory, file_name])
