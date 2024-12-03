"""
DataSources for files created by the Bernese software.
"""

from __future__ import annotations

import os
from typing import Literal

from transformo.core import DataSource


class BerneseCrdDataSource(DataSource):
    """Parse data from a Bernese CRD-file."""

    type: Literal["bernese_crd"] = "bernese_crd"
    filename: os.PathLike | str

    def __init__(self, filename: os.PathLike | str, **kwargs) -> None:
        raise NotImplementedError
