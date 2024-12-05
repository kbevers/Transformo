"""
Presenters related to coordinates.
"""

from __future__ import annotations

import json
from typing import Literal

import numpy as np

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


class ResidualPresenter(Presenter):
    """
    Determine residuals between transformed and target coordinates.
    """

    type: Literal["residual_presenter"] = "residual_presenter"

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._data: dict = {}

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Residuals between the target coordinates and coordinates from final step of
        pipeline.
        """
        stations = results[0].stations
        target = results[-1].coordinate_matrix
        model = results[-2].coordinate_matrix

        residuals = np.subtract(target, model)
        residual_norms = [np.linalg.norm(r) for r in residuals]

        self._data["residuals"] = {}
        for station, residual, norm in zip(stations, residuals, residual_norms):
            self._data["residuals"][station] = list(residual) + [norm]

        self._data["stats"] = {}
        self._data["stats"]["avg"] = list(np.mean(residuals, axis=0)) + [
            np.mean(residual_norms)
        ]
        self._data["stats"]["std"] = list(np.std(residuals, axis=0)) + [
            np.std(residual_norms)
        ]

        print(self._data["stats"])

    def as_json(self) -> str:
        return json.dumps(self._data)

    def as_markdown(self) -> str:
        fmt = "< 10.3g"  # three significant figures, could potentially be an option

        header = ["Station", "Rx", "Ry", "Rz", "Norm"]
        rows = []
        for station, residuals in self._data["residuals"].items():
            row = [station, *[format(r, fmt) for r in residuals]]
            rows.append(row)

        text = (
            "### Station coordinate residuals\n\n"
            "Residuals of the modelled coordinates as compared to "
            "target cooordinates. The table contains simple "
            "differences of the individual coordinate components "
            "as well as the length (norm) of the residual vector.\n\n"
        )
        text += construct_markdown_table(header, rows)

        text += "\n\n### Residual statistics\n"

        header = ["Measure", "Rx", "Ry", "Rz", "Norm"]
        rows = []
        for measure, values in self._data["stats"].items():
            row = [measure, *[format(v, fmt) for v in values]]
            rows.append(row)

        text += "\n"
        text += construct_markdown_table(header, rows)

        return text
