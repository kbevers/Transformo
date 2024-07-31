"""
Transformo - The general purpose tool for determining geodetic transformations
"""

from __future__ import annotations

import logging

import numpy as np
import pydantic
from pydantic.dataclasses import dataclass


# Define project specific expections
class TransformoBaseException(Exception):
    """Base exception for Transformo"""


class TransformoReaderError(TransformoBaseException):
    """Transformo Reader error"""


class TranformoReaderValidationError(TransformoBaseException):
    """Transformo Reader validation error"""


# Logging
console_handler = logging.StreamHandler()
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.setLevel(logging.WARNING)


# Core datatypes
@dataclass(frozen=True)
class Coordinate:
    """Containter for coordinates"""

    # station name
    station: str = pydantic.Field(pattern="[A-z0-9].*", strict=True)

    # timestamp, given as decimalyear
    t: float | None = pydantic.Field(
        None, ge=0.0, le=10000.0, allow_inf_nan=False, strict=True
    )

    # spatial coordinate elements
    x: float = pydantic.Field(allow_inf_nan=False, strict=True)
    y: float = pydantic.Field(allow_inf_nan=False, strict=True)
    z: float = pydantic.Field(allow_inf_nan=False, strict=True)

    wx: float = pydantic.Field(1.0, ge=0.0, le=1.0, allow_inf_nan=False, strict=True)
    wy: float = pydantic.Field(1.0, ge=0.0, le=1.0, allow_inf_nan=False, strict=True)
    wz: float = pydantic.Field(1.0, ge=0.0, le=1.0, allow_inf_nan=False, strict=True)

    @classmethod
    def from_str(
        cls, station: str, t: str, x: str, y: str, z: str, wx: str, wy: str, wz: str
    ) -> Coordinate:
        """ "Instantiate a coordinate from string values"""
        return Coordinate(
            station=station,
            t=float(t),
            x=float(x),
            y=float(y),
            z=float(z),
            wx=float(wx),
            wy=float(wy),
            wz=float(wz),
        )

    @property
    def vector(self) -> np.typing.ArrayLike:
        """Coordinate given as Numpy vector (1D array)."""
        return np.array([self.x, self.y, self.z])

    @property
    def weights(self) -> np.typing.ArrayLike:
        """Weights given as Numpy vector (1D array)."""
        return np.array([self.wx, self.wy, self.wz])
