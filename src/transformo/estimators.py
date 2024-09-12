"""
Transformo estimator classes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Iterable, Literal

import numpy as np
import pydantic

from transformo.protocols import CoordinateMatrix


class Operator(pydantic.BaseModel):
    """Base Operator class."""

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "operator"
    else:
        type: Literal["operator"] = "operator"

    # User-specified name of the DataSource, for easy referencing
    # when overriding settings
    name: str | None = None

    # Kan en TypedDict bruges her? En generisk defineres her og specificeres nærmere
    # i nedarvende klasser? Se https://docs.pydantic.dev/2.3/usage/types/dicts_mapping/#typeddict
    # parameters: Dict[str, float | str | None] | None

    def __init__(
        self,
        name: str | None = None,
        parameters: Dict[str, float | str] | None = None,
        **kwargs,
    ) -> None:
        """Set up base estimator."""

        # if parameters is None:
        #    parameters = {}

        # super().__init__(name=name, parameters=parameters, **kwargs)
        super().__init__(name=name, **kwargs)

    @classmethod
    def get_subclasses(cls) -> Iterable[type[Estimator]]:
        """
        Return a tuple of all known subclasses to `Estimator`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the Pipeline class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "estimator" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [Estimator] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @abstractmethod
    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Operator.

        Abstract. Needs to be implemented by inheriting classes.
        """

    '''
    @property
    def has_parameters(self) -> bool:
        """
        Returns True if parameters are
        """
        return True
    '''


class Transformation(Operator):
    """
    .
    """

    if TYPE_CHECKING:
        type: Any = "transformation"
    else:
        type: Literal["transformation"] = "transformation"


class DummyTransformation(Transformation):
    """
    This Transformation is a dumb dumb.
    """

    type: Literal["dummy_transformation"] = "dummy_transformation"

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Transformation.

        Basically re-defining the same abstract method from the parent class.
        """
        return coordinates


class Estimator(Operator):
    """
    .
    """

    if TYPE_CHECKING:
        type: Any = "estimator"
    else:
        type: Literal["estimator"] = "estimator"

    @abstractmethod
    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """
        Estimate parameters.

        For the base TransformoEstimator class this method does nothing.
        """


class DummyEstimator(Estimator):
    """
    This Estimator is a dumb dumb.
    """

    type: Literal["dummy_estimator"] = "dummy_estimator"

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Transformation.
        """
        return coordinates

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """."""


class Helmert3ParameterEstimator(Estimator):
    """
    The 3 paramter Helmert transformation is a simple translation in the three
    principal directions of a earth-centered, earth-fixed coordinate system (or
    a similarly shaped celestial body). A coordinate in vector Va is transformed
    into vector Vb using the expression below:

        Vb = T + Va

    Where T consist of the three translation parameters, that can be estimated
    using this class.
    """

    type: Literal["helmert3parameter"] = "helmert3parameter"

    def __init__(self, **kwargs) -> None:
        """Set up for Helmert3ParameterEstimator."""
        super().__init__(**kwargs)

        # self.parameters = {"x": None, "y": None, "z": None}

    '''
    @property
    def T(self) -> np.typing.ArrayLike:
        """
        The translation parameters as a vector.
        """
        return np.array([
            self.parameters["x"],
            self.parameters["y"],
            self.parameters["z"],
        ])
    '''

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the 3 parameter Helmert.
        """
        # return coordinates+self.T
        return coordinates

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """
        Estimate parameters.
        """

        coordinate_differences = target_coordinates - source_coordinates
        mean_translation = np.mean(coordinate_differences, axis=0)

        # self.parameters["x"] = mean_translation[0]
        # self.parameters["y"] = mean_translation[1]
        # self.parameters["z"] = mean_translation[2]

        # residuals = target_coordinates - self.forward(source_coordinates)
        # print(source_coordinates)
        # print(target_coordinates)
        # print(coordinate_differences)
        # print(residuals)
