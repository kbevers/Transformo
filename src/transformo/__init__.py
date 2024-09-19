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


class TransformoNotImplemented(TransformoBaseException):
    """
    This is thrown when a "soft abstract" method is not implemented.
    """


class TransformoReaderError(TransformoBaseException):
    """Transformo Reader error"""


class TranformoReaderValidationError(TransformoBaseException):
    """Transformo Reader validation error"""


class TransformoParametersInvalidException(TransformoBaseException):
    """Parameters not initialized correctly."""


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

    # standard deviations, uncertainties
    sx: float = pydantic.Field(ge=0.0, allow_inf_nan=False, strict=True)
    sy: float = pydantic.Field(ge=0.0, allow_inf_nan=False, strict=True)
    sz: float = pydantic.Field(ge=0.0, allow_inf_nan=False, strict=True)

    # coordinate weight
    w: float = pydantic.Field(1.0, ge=0.0, le=1.0, allow_inf_nan=False, strict=True)

    @classmethod
    def from_str(
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
    ) -> Coordinate:
        """ "Instantiate a coordinate from string values"""
        return Coordinate(
            station=station,
            t=float(t),
            x=float(x),
            y=float(y),
            z=float(z),
            sx=float(sx),
            sy=float(sy),
            sz=float(sz),
            w=float(w),
        )

    @property
    def vector(self) -> np.typing.ArrayLike:
        """Coordinate given as Numpy vector (1D array)."""
        return np.array([self.x, self.y, self.z])

    @property
    def stddev(self) -> np.typing.ArrayLike:
        """
        Coordinate standard deviations gives as a Numpy vector (1D array).
        """
        return np.array([self.sx, self.sy, self.sz])

    @property
    def weights(self) -> np.typing.ArrayLike:
        """
        Weights given as Numpy vector (1D array).

        Weights are calculated as the inverse of the standard deviation on each
        coordinate element multiplied by the weight supplied in Coordinate.w.
        """
        weights = np.divide(1, self.stddev)

        return np.multiply(weights, self.w)
