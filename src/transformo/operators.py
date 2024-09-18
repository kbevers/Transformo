"""
Transformo operator classes.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal, Optional

import numpy as np
import pydantic

from transformo import TransformoParametersInvalidException
from transformo.protocols import CoordinateMatrix, Vector


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

    def __init__(
        self,
        name: str | None = None,
        **kwargs,
    ) -> None:
        """Set up base operator."""
        super().__init__(name=name, **kwargs)

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
    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Operator.

        Abstract. Needs to be implemented by inheriting classes.
        """

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

        For the base Operator class this method does nothing.
        """

    '''
    @property
    def has_parameters(self) -> bool:
        """
        Returns True if parameters are
        """
        return True
    '''


class DummyOperator(Operator):
    """
    This Operator is a dumb dumb.
    """

    type: Literal["dummy_operator"] = "dummy_operator"

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """."""

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Transformation.

        It simply returns the same coordinates as it receives. That's how dumb this operation is!
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
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    def __valid_parameters(self) -> bool:
        """Returns True when parameters are valid."""
        return self.x is not None or self.y is not None or self.z is not None

    @property
    def T(self) -> Vector:
        """
        The translation parameters as a vector.
        """
        if not self.__valid_parameters():
            raise TransformoParametersInvalidException(
                "Parameters x, y and z can not be None"
            )

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
        if not self.__valid_parameters():
            raise TransformoParametersInvalidException(
                "Parameters x, y and z can not be None"
            )

        return coordinates + self.T

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
