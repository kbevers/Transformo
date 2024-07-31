"""Protocols for Transformo"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from transformo import Coordinate


class DataSourceLike(Protocol):
    """Protocol for TransformoReaders."""

    coordinates: list[Coordinate]

    def __init__(self, coordinates: list[Coordinate] | None = None) -> None:
        """..."""

    def __add__(self, other) -> DataSourceLike:
        """..."""

    @property
    def coordinate_matrix(self) -> np.typing.ArrayLike:
        """..."""
