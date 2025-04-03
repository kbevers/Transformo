"""
Presenters related to coordinates.
"""

from __future__ import annotations

import json
import pathlib
from enum import Enum
from typing import Literal

import numpy as np

from transformo.core import DataSource, Operator, Presenter
from transformo.transformer import Transformer

from . import construct_markdown_table


def _raise_exception_if_file_cant_be_created(filename: pathlib.Path):
    """Throws a FileNotFoundError if the file can't be opened"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("")
    # open() will raise the exception, so we don't have to re-raise it here
    # but we still need to clean up:
    finally:
        if filename.exists():
            filename.unlink()


class CoordinateType(Enum):
    """
    Defines coordinate archetypes.
    """

    CARTESIAN = "cartesian"
    DEGREES = "degrees"
    PROJECTED = "projected"


class CoordinatePresenter(Presenter):
    """
    Create lists of coordinates for all stages of a pipeline.
    """

    type: Literal["coordinate_presenter"] = "coordinate_presenter"
    json_file: pathlib.Path | None = None
    geojson_file: pathlib.Path | None = None

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._operator_titles: list[str] = []
        self._steps: list[dict[str, list[float | None]]] = []

        if self.json_file:
            _raise_exception_if_file_cant_be_created(self.json_file)

        if self.geojson_file:
            _raise_exception_if_file_cant_be_created(self.geojson_file)
            self._geojson_features: list[dict] = []

    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
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
        for ds in [source_data, *results, target_data]:
            data = {}
            for c in ds.coordinates:
                data[c.station] = [c.x, c.y, c.z, c.t]
            steps.append(data)

        self._steps = steps

        operator_titles = []
        for operator in operators:
            operator_titles.append(repr(operator))

        self._operator_titles = operator_titles

        if self.geojson_file:
            for coordinate in target_data.coordinates:
                self._geojson_features.append(coordinate.geojson_feature())

    def as_json(self) -> str:
        return json.dumps(self._steps)

    def create_json_file(self) -> None:
        """Output data as a JSON-file"""
        if self.json_file:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self._steps, f)

    def create_geojson_file(self) -> None:
        """Output data as a GeoJSON-file."""

        if not self.geojson_file:
            return None

        # prepare data structure
        for feature in self._geojson_features:
            key = feature["properties"]["station"]
            for i, step in enumerate(self._steps):
                x, y, z, _ = step[key]
                postfix = str(i)
                if i == 0:
                    postfix = "source"
                if i == len(self._steps) - 1:
                    postfix = "target"

                feature["properties"][f"x_{postfix}"] = x
                feature["properties"][f"y_{postfix}"] = y
                feature["properties"][f"z_{postfix}"] = z

        geojson = {
            "type": "FeatureCollection",
            "features": self._geojson_features,
        }

        with open(self.geojson_file, "w", encoding="utf-8") as f:
            json.dump(geojson, f)

        return None

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

    coordinate_type: CoordinateType
    json_file: pathlib.Path | None = None
    geojson_file: pathlib.Path | None = None

    def __init__(self, coordinate_type: CoordinateType, **kwargs) -> None:
        """."""
        super().__init__(coordinate_type=coordinate_type, **kwargs)

        if self.json_file:
            _raise_exception_if_file_cant_be_created(self.json_file)
        if self.geojson_file:
            _raise_exception_if_file_cant_be_created(self.geojson_file)
            self._geojson_features: list[dict] = []

        # set up degrees -> cartesian converter
        self._cart_transformer = Transformer.from_projstring("+proj=cart +ellps=GRS80")
        self._cart_transformer_inv = Transformer.from_projstring(
            "+proj=cart +ellps=GRS80 +inv"
        )

        self._data: dict = {}

    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        """
        Residuals between the target coordinates and coordinates from final step of
        pipeline.
        """
        stations = results[0].stations
        target = target_data.coordinate_matrix
        model = results[-1].coordinate_matrix

        residuals = np.subtract(target, model)

        # convert to milimeters
        residuals *= 1000

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

        if self.geojson_file:
            transformer = None
            if self.coordinate_type == CoordinateType.CARTESIAN:
                transformer = self._cart_transformer_inv

            for coordinate in target_data.coordinates:
                self._geojson_features.append(
                    coordinate.geojson_feature(transformer=transformer)
                )

    def as_json(self) -> str:
        return json.dumps(self._data)

    def create_json_file(self) -> None:
        """Output data as a JSON-file"""
        if self.json_file:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f)

    def create_geojson_file(self) -> None:
        """Output data as a GeoJSON-file."""

        if not self.geojson_file:
            return None

        # prepare data structure
        for feature in self._geojson_features:
            key = feature["properties"]["station"]
            x, y, z, norm = self._data["residuals"][key]

            feature["properties"]["residual_x"] = x
            feature["properties"]["residual_y"] = y
            feature["properties"]["residual_z"] = z
            feature["properties"]["residual_total"] = norm

        geojson = {
            "type": "FeatureCollection",
            "features": self._geojson_features,
        }

        with open(self.geojson_file, "w", encoding="utf-8") as f:
            json.dump(geojson, f)

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


class TopocentricResidualPresenter(Presenter):
    """
    Determine topocentric residuals between transformed and target coordinates.

    Three types of coordinates are know to Transformo:

        Degrees:    Latitude, longitude, height above ellipsoid
        Cartesian:  Geocentric, cartesian coordinates. Also known as ECEF.
        Projected:  Coordinates in a projected CRS.

    Residuals are given as differences in the north (N), east (E) and up (U)
    components. Coordinates of types degrees and cartesian

    Projected coordinates are assumed to already be somewhat topocentric, and
    will not be manipulated before the residuals are calculated.
    """

    type: Literal["topocentricresidual_presenter"] = "topocentricresidual_presenter"

    coordinate_type: CoordinateType
    json_file: pathlib.Path | None = None
    geojson_file: pathlib.Path | None = None

    def __init__(self, coordinate_type: CoordinateType, **kwargs) -> None:
        """."""
        super().__init__(coordinate_type=coordinate_type, **kwargs)

        if self.json_file:
            _raise_exception_if_file_cant_be_created(self.json_file)
        if self.geojson_file:
            _raise_exception_if_file_cant_be_created(self.geojson_file)
            self._geojson_features: list[dict] = []

        self._data: dict = {}

        # set up degrees -> cartesian converter
        self._cart_transformer = Transformer.from_projstring("+proj=cart +ellps=GRS80")
        self._cart_transformer_inv = Transformer.from_projstring(
            "+proj=cart +ellps=GRS80 +inv"
        )

    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        """
        Residuals between the target coordinates and coordinates from final step of
        pipeline.
        """
        stations = results[0].stations
        target = target_data.coordinate_matrix
        model = results[-1].coordinate_matrix

        if self.coordinate_type in (CoordinateType.DEGREES, CoordinateType.CARTESIAN):
            # We can leverage PROJ's "topocentric" operation for this.
            # When the topocentric origin is set to the target coordinate,
            # we can feed the transformed coordinate to the operation which
            # will then return the topocentric residual.
            # It goes something like this:
            #   echo 3513638.5518 778956.1856 5248216.2445 | cct +proj=topocentric \
            #     +X_0=3513638.5605 +Y_0=778956.1839 +Z_0=5248216.2482
            if self.coordinate_type == CoordinateType.DEGREES:
                target = self._cart_transformer.transform_many(target)
                model = self._cart_transformer.transform_many(model)

            templist = []
            for m, t in zip(model, target):
                pipeline = f"+proj=topocentric +ellps=GRS80 +X_0={t[0]} +Y_0={t[1]} +Z_0={t[2]}"
                enu_diffs = Transformer.from_projstring(pipeline).transform_one(m)
                templist.append(np.array(enu_diffs))
                residuals = np.array(templist)

        if self.coordinate_type == CoordinateType.PROJECTED:
            residuals = np.subtract(target, model)

        # convert residual values to mm
        residuals *= 1000

        # calculate norms, results in mm
        norms_2d = [np.linalg.norm((r[0], r[1])) for r in residuals]
        norms_3d = [np.linalg.norm(r) for r in residuals]

        self._data["residuals"] = {}
        for station, residual, norm2d, norm3d in zip(
            stations, residuals, norms_2d, norms_3d
        ):
            self._data["residuals"][station] = list(residual) + [norm2d] + [norm3d]

        self._data["stats"] = {}
        self._data["stats"]["avg"] = (
            list(np.mean(residuals, axis=0)) + [np.mean(norms_2d)] + [np.mean(norms_3d)]
        )
        self._data["stats"]["std"] = (
            list(np.std(residuals, axis=0)) + [np.std(norms_2d)] + [np.mean(norms_3d)]
        )

        if self.geojson_file:
            transformer = None
            if self.coordinate_type == CoordinateType.CARTESIAN:
                transformer = self._cart_transformer_inv

            for coordinate in target_data.coordinates:
                self._geojson_features.append(
                    coordinate.geojson_feature(transformer=transformer)
                )

    def as_json(self) -> str:
        return json.dumps(self._data)

    def create_json_file(self) -> None:
        """Output data as a JSON-file"""
        if not self.json_file:
            return None

        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f)

    def create_geojson_file(self) -> None:
        """Output data as a GeoJSON-file."""

        if not self.geojson_file:
            return None

        # prepare data structure
        for feature in self._geojson_features:
            key = feature["properties"]["station"]
            x, y, z, norm_2d, norm_3d = self._data["residuals"][key]

            feature["properties"]["residual_n"] = x
            feature["properties"]["residual_e"] = y
            feature["properties"]["residual_u"] = z
            feature["properties"]["residual_planar"] = norm_2d
            feature["properties"]["residual_total"] = norm_3d

        geojson = {
            "type": "FeatureCollection",
            "features": self._geojson_features,
        }

        with open(self.geojson_file, "w", encoding="utf-8") as f:
            json.dump(geojson, f)

    def as_markdown(self) -> str:
        fmt = "< 10.3g"  # three significant figures, could potentially be an option

        header = ["Station", "North", "East", "Up", "Planar residual", "Total residual"]
        rows = []
        for station, residuals in self._data["residuals"].items():
            row = [station, *[format(r, fmt) for r in residuals]]
            rows.append(row)

        text = (
            "### Station coordinate residuals\n\n"
            "Residuals in topocentric space of the modelled coordinates as "
            "compared to target cooordinates. The table contains coordinate "
            "differences of the individual coordinate components "
            "as well as the length (norm) of the residual vector, "
            "both in the plane and across all dimensions.\n\n"
        )
        text += construct_markdown_table(header, rows)

        text += "\n\n### Residual statistics\n"

        header = ["Measure", "North", "East", "Up", "Planar residual", "Total residual"]
        rows = []
        for measure, values in self._data["stats"].items():
            row = [measure, *[format(v, fmt) for v in values]]
            rows.append(row)

        text += "\n"
        text += construct_markdown_table(header, rows)

        return text
