"""Type annotations for Transformo"""

from __future__ import annotations

from typing import Annotated, Literal

import numpy as np
import numpy.typing as npt

Vector = Annotated[npt.NDArray[np.floating], Literal[3, 1]]
CoordinateMatrix = Annotated[npt.NDArray[np.floating], Literal["N", 3]]

ParameterValue = str | float | None
