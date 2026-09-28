"""Resolve launch substitutions embedded in YAML parameter files."""

from __future__ import annotations

import re
import tempfile
from collections.abc import Mapping, Sequence
from typing import Any

import launch
from launch.substitutions import LaunchConfiguration


class YamlParamsResolver(launch.Substitution):
    """Write a temporary YAML file with ``{{parameter}}`` values resolved."""

    def __init__(
        self,
        source_file: launch.SomeSubstitutionsType,
        launch_params: Sequence[Mapping[str, Any]] | None = None,
        param_rewrites: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__()
        from launch.utilities import normalize_to_list_of_substitutions

        self._source_file = normalize_to_list_of_substitutions(source_file)
        self._launch_params = launch_params or []
        self._param_rewrites = {
            key: normalize_to_list_of_substitutions(value)
            for key, value in (param_rewrites or {}).items()
        }
        self._parameter_pattern = re.compile(r"\{\{(.*?)\}\}")

    def perform(self, context: launch.LaunchContext) -> str:
        """Resolve the source YAML file and return a temporary rewritten path."""
        yaml_path = launch.utilities.perform_substitutions(
            context,
            self._source_file,
        )
        with open(yaml_path, encoding="utf-8") as source_file:
            source = source_file.read()

        rewritten = self._substitute_params(
            source,
            self._resolve_params(context),
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            encoding="utf-8",
            suffix=".yaml",
        ) as output_file:
            output_file.write(rewritten)
            return output_file.name

    def _resolve_params(self, context: launch.LaunchContext) -> dict[str, str]:
        resolved = {
            parameter["name"]: launch.utilities.perform_substitutions(
                context,
                [LaunchConfiguration(parameter["name"])],
            )
            for parameter in self._launch_params
        }
        for name, substitutions in self._param_rewrites.items():
            resolved[name] = launch.utilities.perform_substitutions(
                context,
                substitutions,
            )
        return resolved

    def _substitute_params(
        self,
        source: str,
        replacements: Mapping[str, str],
    ) -> str:
        """Replace every ``{{parameter}}`` expression in the YAML source."""
        def replacement(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in replacements:
                raise KeyError(
                    f"Parameter {name!r} is not available for YAML substitution."
                )
            return replacements[name]

        return self._parameter_pattern.sub(replacement, source)
