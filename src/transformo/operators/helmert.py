"""
Helmert operators.
"""

from __future__ import annotations

import math
from typing import Literal, Optional

import numpy as np

from transformo._typing import CoordinateMatrix, Vector
from transformo.core import Operator
from transformo.datatypes import Parameter


# MyPy acts up a bit when encountering class variables that are Optional.
# When we have a pydantic.BaseModel with a class variable such as
#
#    x: Optional[float] = float("nan")
#
# MyPy will think of it having type "float | None", which is likely correct
# but a bit of a pain, since many functions that work on floats have their
# input types set to "float". MyPy will complain when the class variable is
# passed to `float()` etc. By wrapping these functions with a guard for None
# MyPy accepts input of type "float | None" since they effective strip the None
# part of the variables typing information.
def _isnan(f: float | None) -> bool:
    if f is None:
        f = float("nan")
    return math.isnan(f)


def _float(f: float | None) -> float:
    if f is None:
        f = float("nan")
    return float(f)


class HelmertTranslation(Operator):
    """
    The 3 paramter Helmert transformation is a simple translation in the three
    principal directions of a earth-centered, earth-fixed coordinate system (or
    a similarly shaped celestial body). A coordinate in vector Va is transformed
    into vector Vb using the expression below:

        Vb = T + Va

    Where T consist of the three translation parameters, that can be estimated
    using this class.
    """

    type: Literal["helmert_translation"] = "helmert_translation"

    # Parameters
    x: Optional[float] = float("nan")
    y: Optional[float] = float("nan")
    z: Optional[float] = float("nan")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # if one or more parameter is given at instantiation time
        if not _isnan(self.x) or not _isnan(self.y) or not _isnan(self.z):
            self._transformation_parameters_given = True

        self._sanitize_parameters()
        # ... from now on we can rely on parameters being useful

    def _sanitize_parameters(self) -> None:
        """Make sure that translation parameters are not None."""
        if _isnan(self.x):
            self.x = 0.0

        if _isnan(self.y):
            self.y = 0.0

        if _isnan(self.z):
            self.z = 0.0

    def _proj_name(self) -> str:
        if not self.parameters:
            # In principle PROJ will accept a "+proj=helmert" string without
            # parameters, but this will be slightly faster and communicate
            # better that nothing is done
            return "noop"

        return "helmert"

    def _parameter_list(self) -> list[Parameter]:
        params: list[Parameter] = []
        if not _isnan(self.x) and self.x != 0.0:
            params.append(Parameter("x", _float(self.x)))

        if not _isnan(self.y) and self.y != 0.0:
            params.append(Parameter("y", _float(self.y)))

        if not _isnan(self.z) and self.z != 0.0:
            params.append(Parameter("z", _float(self.z)))

        return params

    @property
    def T(self) -> Vector:
        """
        The translation parameters as a vector.
        """
        return np.array(
            [
                self.x,
                self.y,
                self.z,
            ]
        )

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the 3 parameter Helmert.
        """
        return coordinates + self.T

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the 3 parameter Helmert.
        """
        return coordinates - self.T

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """
        Estimate parameters.

        Parameters `x`, `y` and `z` of this operator *will* be overwritten once
        this method is called.

        Weights for source and target coordinates are ignored.
        """

        coordinate_differences = target_coordinates - source_coordinates
        mean_translation = np.mean(coordinate_differences, axis=0)

        self.x = mean_translation[0]
        self.y = mean_translation[1]
        self.z = mean_translation[2]
