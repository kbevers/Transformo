"""
Transformo operator classes.
"""

from __future__ import annotations

import math
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal, Optional, Protocol

import numpy as np
import pydantic

from transformo.typing import CoordinateMatrix, ParameterValue, Vector


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


class OperatorLike(Protocol):
    """Protocal for Transformo Operator classes."""

    type: Any

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """Forward method of the Operator."""


class Operator(pydantic.BaseModel):
    """
    Base Operator class.

    Operators are essential building blocks for the Pipeline. All operators
    have the ability to manipulate coordinates, generally in the sense of a geodetic
    transformation. In addition operators *can* implement a method to derive
    parameters for said coordinate operation. Most Operators do, but not all.

    So, Operators have two principal modes of operation:

        1. Coordinate operations, as defined in the ISO 19111 terminology
        2. Estimating parameters for the coordinate operations

    The abilities of a Operator are determined by the methods that enheriting classes
    implement. *All* Operator's must implement the `forward` method and they *can*
    implement the `estimate` and `inverse` methods. If only the `forward` method is
    implemented the operator will exist as a coordinate operation that can't
    estimate parameters.
    """

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "operator"
    else:
        type: Literal["operator"] = "operator"

    # User-specified name of the Operator, for easy referencing
    # when overriding settings etc.
    name: str | None = None

    def __init__(
        self,
        name: str | None = None,
        **kwargs,
    ) -> None:
        """Set up base operator."""
        super().__init__(name=name, **kwargs)

        self._transformation_parameters_given: bool = False

    def __repr__(self) -> str:
        """ """
        params = ", ".join(f"{k}: {v}" for k, v in self.parameters.items())
        return self.__class__.__name__ + f"({params})"

    @classmethod
    def get_subclasses(cls) -> Iterable[type[Operator]]:
        """
        Return a tuple of all known subclasses to `Operator`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the Pipeline class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "operator" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [Operator] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @abstractmethod
    def _proj_name(self) -> str:
        """Helper for the `proj_operation_name` property."""

    @abstractmethod
    def _parameter_dict(self) -> dict[str, ParameterValue]:
        """Helper for the `parameters` property."""

    @property
    def can_estimate(self) -> bool:
        """
        Determine if an `Operator` is able to estimate parameters or not.

        An operator can be unfit for estimating parameters in two ways:

            1. The `estimate()` method is not implemented
        or
            2. The `Operator` was invoked with parameters that would otherwise
               need to be estimated

        In the last case the operator will only be used to convert coordinates
        using the `forward()` method of the `Operator`.
        """
        if self._transformation_parameters_given:
            return False

        # If we get to here, no parameters were supplied by the user and
        # we are expected to estimate them. We don't want to spend to much
        # energy on this, so simple coordinate and weight matrices are
        # given as input. If `estimate()` is implemented *some* parameters
        # will be estimated and stored in the `Operator` but they will be
        # discarded when `estimate()` is executed again with proper input.
        zero_matrix = np.zeros(shape=(4, 3))
        try:
            self.estimate(zero_matrix, zero_matrix, zero_matrix, zero_matrix)
        except NotImplementedError:
            return False

        return True

    @property
    def proj_operation_name(self) -> str:
        """
        Return the name of the PROJ operation that relates to
        the Transformo Operator.
        """
        return self._proj_name()

    @property
    def parameters(self) -> dict[str, ParameterValue]:
        """
        Return parameters in a standardized way.

        Parameters are returned as a dict with the parameter names given as
        the keys with their corresponding values. Parameter names in the keys
        are generally meant to be the same as they would be in PROJ (without the
        +'s).

        Following PROJ conventions, a parameter entry be on one of the following
        forms:

            1. +param=number
            2. +param=string
            3. +

        Abstract method. Needs to be implemented by inheriting classes.
        """
        return self._parameter_dict()

    @abstractmethod
    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Operator.

        Abstract. Needs to be implemented by inheriting classes.
        """

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the Operator.

        Abstract. Can be implemented by inheriting classes.
        """
        raise NotImplementedError

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """
        Estimate parameters.

        Abstract. Can be implemented by inheriting classes.
        """
        raise NotImplementedError


class DummyOperator(Operator):
    """
    This Operator is a dumb dumb.

    Its primary function is to be useful in testing scenarios.
    """

    type: Literal["dummy_operator"] = "dummy_operator"

    def _parameter_dict(self) -> dict[str, ParameterValue]:
        return {}

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

    def _parameter_dict(self) -> dict[str, ParameterValue]:
        params: dict[str, ParameterValue] = {}
        if not _isnan(self.x) and self.x != 0.0:
            params["x"] = _float(self.x)

        if not _isnan(self.y) and self.y != 0.0:
            params["y"] = _float(self.y)

        if not _isnan(self.z) and self.z != 0.0:
            params["z"] = _float(self.z)

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
