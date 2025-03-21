"""
Transformo operator classes.
"""

from __future__ import annotations

from typing import Literal

from transformo._typing import CoordinateMatrix
from transformo.core import Operator
from transformo.datatypes import Parameter

from .helmert import Helmert7Param, HelmertTranslation, RotationConvention
from .proj import ProjOperator

__all__ = [
    "Operator",
    "DummyOperator",
    "HelmertTranslation",
    "Helmert7Param",
    "RotationConvention",
    "ProjOperator",
]


class DummyOperator(Operator):
    """
    This Operator is a dumb dumb.

    Its primary function is to be useful in testing scenarios.
    """

    type: Literal["dummy_operator"] = "dummy_operator"

    def _parameter_list(self) -> list[Parameter]:
        return []

    def _proj_name(self) -> str:
        return "noop"

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """This does absolutely nothing. Yes, it's dumb."""

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Transformation.

        It simply returns the same coordinates as it receives.
        That's how dumb this operation is!
        """
        return coordinates

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the Transformation.

        It simply returns the same coordinates as it receives.
        That really is how dumb this operation is!
        """
        return coordinates
