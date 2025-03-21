"""
Helmert operators.
"""

from __future__ import annotations

import enum
import math
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal, Optional

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

        # determine if the operation can estimate parameters or not
        self._has_transformation_parameters_been_given()

        self._sanitize_parameters()
        # ... from now on we can rely on parameters being useful

    def _has_transformation_parameters_been_given(self):
        """
        Part of the __init__ process. Supports DataSource.can_estimate

        This exist as its own method so it can be overridden in a classes
        enheriting from HelmertTranslation.
        """
        # if one or more parameter is given at instantiation time
        if not _isnan(self.x) or not _isnan(self.y) or not _isnan(self.z):
            self._transformation_parameters_given = True

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
    def T(self) -> Vector:  # pylint: disable=invalid-name
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

        avg_source = np.average(source_coordinates, axis=0, weights=source_weights)
        avg_target = np.average(target_coordinates, axis=0, weights=target_weights)

        mean_translation = avg_target - avg_source

        self.x = mean_translation[0]
        self.y = mean_translation[1]
        self.z = mean_translation[2]


class RotationConvention(enum.Enum):
    """
    Rotation convention of Helmert transformations.
    """

    POSITION_VECTOR = "position_vector"
    COORDINATE_FRAME = "coordinate_frame"


class Helmert7Param(HelmertTranslation):
    """
    The 7 paramter Helmert transformation performs a translation in the three
    principal directions of a earth-centered, earth-fixed coordinate system (or
    a similarly shaped celestial body), as well as rotations around those axes
    and a scaling of the coordinates.
    """

    # mypy will complain since HelmertTrainslation defines this as
    # a Literal["helmert_translation"], so we have it look the other
    # way for a brief moment when checking the types.
    if TYPE_CHECKING:
        type: Any = "helmert_7param"
    else:
        type: Literal["helmert_7param"] = "helmert_7param"

    convention: RotationConvention
    small_angle_approximation: bool = True

    # Rotation parameters - given in arc seconds
    rx: Optional[float] = float("nan")
    ry: Optional[float] = float("nan")
    rz: Optional[float] = float("nan")

    # Scale parameter - given in ppm
    s: Optional[float] = float("nan")

    def __init__(self, convention: RotationConvention, **kwargs) -> None:
        super().__init__(convention=convention, **kwargs)

    def _has_transformation_parameters_been_given(self):
        # if one or more parameter is given at instantiation time
        parameters_instantiated = [
            not _isnan(self.x),
            not _isnan(self.y),
            not _isnan(self.z),
            not _isnan(self.rx),
            not _isnan(self.ry),
            not _isnan(self.rz),
            not _isnan(self.s),
        ]

        if any(parameters_instantiated):
            self._transformation_parameters_given = True

    def _sanitize_parameters(self) -> None:
        """Make sure that translation parameters are not None."""
        super()._sanitize_parameters()

        if _isnan(self.rx):
            self.rx = 0.0

        if _isnan(self.ry):
            self.ry = 0.0

        if _isnan(self.rz):
            self.rz = 0.0

        if _isnan(self.s):
            self.s = 0.0

    def _parameter_list(self) -> list[Parameter]:
        params: list[Parameter] = super()._parameter_list()

        if not _isnan(self.rx) and self.rx != 0.0:
            params.append(Parameter("rx", _float(self.rx)))

        if not _isnan(self.ry) and self.ry != 0.0:
            params.append(Parameter("ry", _float(self.ry)))

        if not _isnan(self.rz) and self.rz != 0.0:
            params.append(Parameter("rz", _float(self.rz)))

        if not _isnan(self.s) and self.s != 0.0:
            params.append(Parameter("s", _float(self.s)))

        params.append(Parameter("convention", self.convention.value))
        if self.small_angle_approximation:
            params.append(Parameter("approx"))

        return params

    @cached_property
    def R(self) -> CoordinateMatrix:  # pylint: disable=invalid-name
        """
        Rotation matrix.
        """

        def arcsec2rad(arcsec) -> float:
            return np.deg2rad(arcsec) / 3600.0

        rx = arcsec2rad(self.rx)
        ry = arcsec2rad(self.ry)
        rz = arcsec2rad(self.rz)

        if self.small_angle_approximation:

            rotation_matrix = np.array(
                [
                    [1, -rz, ry],
                    [rz, 1, -rx],
                    [-ry, rx, 1],
                ]
            )
        else:
            # fmt: off
            cos = np.cos
            sin = np.sin
            Rx = np.array( # pylint: disable=invalid-name
                [
                    [1,       0,        0],
                    [0, cos(rx), -sin(rx)],
                    [0, sin(rx),  cos(rx)],
                ]
            )
            Ry = np.array( # pylint: disable=invalid-name
                [
                    [ cos(ry),  0,  sin(ry)],
                    [       0,  1,        0],
                    [-sin(ry),  0,  cos(ry)],
                ]
            )
            Rz = np.array( # pylint: disable=invalid-name
                [
                    [cos(rz), -sin(rz), 0],
                    [sin(rz),  cos(rz), 0],
                    [      0,        0, 1],
                ]
            )
            # fmt: on
            rotation_matrix = Rz @ Ry @ Rx

        if self.convention == RotationConvention.POSITION_VECTOR:
            return rotation_matrix

        # If the convention is not position vector convention it must be
        # coordinate frame which we get by transposing the rotation matrix
        return rotation_matrix.T

    @property
    def scale(self) -> float:
        """Scale parameter, given in SI units."""
        if self.s is None:
            return 1
        return 1 + self.s * 1e-6

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the 7 parameter Helmert.
        """

        # Since the coordinates are contained in a Nx3 matrix, we deviate
        # from the single-point Helmert formulation of B = T + s * R*A.
        # By transposing the rotation matrix we get the same results
        # when instead doing B = T + s * A*R^T.
        return self.T + self.scale * coordinates @ self.R.T

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the 7 parameter Helmert.
        """
        return -self.T + 1 / self.scale * coordinates @ self.R
