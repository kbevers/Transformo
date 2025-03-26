"""
Wrapper for pyproj, that fits the patterns of Transformo.
"""

from __future__ import annotations

import numpy as np
import pyproj

from transformo._typing import CoordinateMatrix, Vector


class Transformer:
    """
    Transform coordinates using PROJ.

    Interface for pyproj that works using Transformo's datatypes such
    as CoordinateMatrix and Vector.
    """

    def __init__(self, transformer: pyproj.Transformer | None = None):
        """
        Initialize a Transformer.

        If None is passed to the method a generic "noop" PROJ transformation
        is created.

        Generally advised to instantiate `Transformer`s using class methods
        such as `from_projstring`.
        """
        if not transformer:
            self.transformer = pyproj.Transformer.from_pipeline("+proj=noop")
        else:
            self.transformer = transformer

    @classmethod
    def from_projstring(cls, projstring: str):
        """
        Instantiate a `Transformer` using a PROJ string.

        Any valid PROJ string can be used.
        """
        transformer = pyproj.Transformer.from_pipeline(projstring)
        return Transformer(transformer=transformer)

    def transform_many(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Transform a CoordinateMatrix.
        """
        results = self.transformer.itransform(coordinates)
        return np.array(list(results))

    def transform_one(self, coordinate: Vector) -> Vector:
        """
        Transform a single coordinate.
        """
        (x, y, z) = self.transformer.transform(
            xx=coordinate[0], yy=coordinate[1], zz=coordinate[2]
        )

        return np.array((x, y, z))
