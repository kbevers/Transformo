"""Protocols for Transformo"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Protocol

import numpy as np
import numpy.typing as npt

from transformo import Coordinate

Vector = Annotated[npt.NDArray[np.floating], Literal[3, 1]]
CoordinateMatrix = Annotated[npt.NDArray[np.floating], Literal["N", 3]]


class DataSourceLike(Protocol):
    """Protocol for TransformoReaders."""

    type: Any
    coordinates: list[Coordinate]

    def __init__(self, coordinates: list[Coordinate] | None = None) -> None:
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
