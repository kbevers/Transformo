"""Type annotations for Transformo"""

# There's no need to add docstrings and lots of methods for the Protocols defined below,
# so we turn of complaints from pylint.
# pylint: disable=missing-function-docstring, too-few-public-methods

from __future__ import annotations

from typing import Annotated, Any, Literal, Protocol

import numpy as np
import numpy.typing as npt

Vector = Annotated[npt.NDArray[np.floating], Literal[3, 1]]
CoordinateMatrix = Annotated[npt.NDArray[np.floating], Literal["N", 3]]

ParameterValue = str | float | None


class CoordinateLike(Protocol):
    """Protocol for Coordinates"""

    station: str
    t: float | None
    x: float
    y: float
    z: float
    sx: float
    sy: float
    sz: float
    w: float

    @classmethod
    def from_str(  # pylint: disable=too-many-arguments
        cls,
        station: str,
        t: str,
        x: str,
        y: str,
        z: str,
        sx: str,
        sy: str,
        sz: str,
        w: str = "1.0",
    ) -> CoordinateLike: ...

    @property
    def vector(self) -> np.typing.ArrayLike: ...

    @property
    def stddev(self) -> np.typing.ArrayLike: ...

    @property
    def weights(self) -> np.typing.ArrayLike: ...


class DataSourceLike(Protocol):
    """Protocol for DataSources."""

    type: Any
    coordinates: list[CoordinateLike]

    def __init__(self, coordinates: list[CoordinateLike] | None = None) -> None:
        """..."""

    def __add__(self, other) -> DataSourceLike:
        """..."""

    @property
    def coordinate_matrix(self) -> CoordinateMatrix:
        """..."""


class OperatorLike(Protocol):
    """Protocal for Transformo Operator classes."""

    type: Any

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """Forward method of the Operator."""


class PresenterLike(Protocol):
    """Protocal for Transformo Presenter classes."""

    type: Any

    def evaluate(
        self, operators: list[OperatorLike], results: list[DataSourceLike]
    ) -> None:
        """
        Store parsed information from operators and resulting datasources in
        internal data container for further processing.
        """
