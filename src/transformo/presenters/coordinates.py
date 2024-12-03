"""
Presenters related to coordinates.
"""

from __future__ import annotations

import json
from typing import Literal

from transformo.core import DataSource, Operator, Presenter

from . import construct_markdown_table


class CoordinatePresenter(Presenter):
    """
    Create lists of coordinates for all stages of a pipeline.
    """

    type: Literal["coordinate_presenter"] = "coordinate_presenter"

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._operator_titles: list[str] = []
        self._steps: list[dict[str, list[float | None]]] = []

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Parse coordinates from `results`.

        Assumptions about DataSources in `results`:

          - they are of the same size
          - cointain coordinates for the same stations across each step
          - are ordered by stations in the same way across each step.

        This should hold true as long as `results` has it's origin in a
        Pipeline.
        """
        steps = []
        for ds in results:
            data = {}
            for c in ds.coordinates:
                data[c.station] = [c.x, c.y, c.z, c.t]
            steps.append(data)

        self._steps = steps

        operator_titles = []
        for operator in operators:
            operator_titles.append(repr(operator))

        self._operator_titles = operator_titles

    def as_json(self) -> str:
        return json.dumps(self._steps)

    def as_markdown(self) -> str:
        fmt = ".4f"
        header = ["Station", "x", "y", "z", "t"]

        text = "Source and target coordinates as well as "
        text += "intermediate results shown in tabular form.\n\n"

        for i, step in enumerate(self._steps):
            if i == 0:
                stepname = "Source coordinates"
            elif i < len(self._steps) - 1:
                stepname = f"Step {i}: {self._operator_titles[i-1]}"
            else:
                stepname = "Target coordinates"

            text += f"### {stepname}\n\n"
            rows = []
            for station, coordinate in step.items():
                row = [station, *[format(c, fmt) for c in coordinate]]
                rows.append(row)

            table = construct_markdown_table(header, rows)

            text += f"{table}\n\n"

        return text.rstrip()
