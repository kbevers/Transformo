"""
Operator(s) based on PROJ.
"""

from __future__ import annotations

import re
from typing import Literal

import numpy as np
import pyproj
import pyproj.enums

from transformo._typing import CoordinateMatrix
from transformo.core import Operator
from transformo.datatypes import Parameter


class ProjOperator(Operator):
    """
    Expose PROJ operations.
    """

    type: Literal["proj_operator"] = "proj_operator"

    proj_string: str

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._transformer = pyproj.Transformer.from_pipeline(self.proj_string)

    def _parameter_list(self) -> list[Parameter]:
        params = []
        for param in self.proj_string.split():
            if param == "+proj=pipeline":
                continue

            params.append(Parameter.from_proj_param(param))

        return params

    def _proj_name(self) -> str:
        matches = re.search(r"^\+?proj=([a-z]+) ", self.proj_string)
        assert matches is not None, "PROJ string is ill-formed"

        return matches.group(1)

    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Transformation.
        """
        x, y, z = self._transformer.transform(
            coordinates[:, 0],
            coordinates[:, 1],
            coordinates[:, 2],
            direction=pyproj.enums.TransformDirection.FORWARD,
        )
        return np.array([x, y, z]).transpose()

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the Transformation.
        """
        x, y, z = self._transformer.transform(
            coordinates[:, 0],
            coordinates[:, 1],
            coordinates[:, 2],
            direction=pyproj.enums.TransformDirection.INVERSE,
        )
        return np.array([x, y, z]).transpose()
