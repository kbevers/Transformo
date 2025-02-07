"""
The CSV DataSource for Transformo.
"""

import csv
import enum
import os
from typing import Literal

import pydantic

from transformo import logger
from transformo.core import DataSource
from transformo.datatypes import Coordinate


class CsvColumns(enum.Enum):
    """Keep track of CSV file column content"""

    SKIP = "skip"
    STATION = "station"
    T = "t"
    X = "x"
    Y = "y"
    Z = "z"
    SX = "sx"
    SY = "sy"
    SZ = "sz"
    W = "weight"


REQUIRED_COLUMNS = (
    CsvColumns.STATION,
    CsvColumns.T,
    CsvColumns.X,
    CsvColumns.Y,
    CsvColumns.Z,
    CsvColumns.SX,
    CsvColumns.SY,
    CsvColumns.SZ,
)


def _dict_to_coordinate(d: dict[str, str]) -> Coordinate:
    weight = 1.0
    if "weight" in d.keys() and d["weight"]:
        weight = float(d["weight"])

    return Coordinate(
        station=d["station"],
        t=float(d["t"]),
        x=float(d["x"]),
        y=float(d["y"]),
        z=float(d["z"]),
        sx=float(d["sx"]),
        sy=float(d["sy"]),
        sz=float(d["sz"]),
        w=weight,
    )


class CsvDataSource(DataSource):
    """Reader for generic CSV-files."""

    type: Literal["csv"] = "csv"
    filename: os.PathLike | str
    columns: list[CsvColumns] = [  # default column order defined here
        CsvColumns.STATION,
        CsvColumns.T,
        CsvColumns.X,
        CsvColumns.Y,
        CsvColumns.Z,
        CsvColumns.SX,
        CsvColumns.SY,
        CsvColumns.SZ,
        CsvColumns.W,
    ]

    @pydantic.field_validator("columns", mode="before")
    @classmethod
    def _validate_columns(cls, columns: list[CsvColumns]) -> list[CsvColumns]:
        """Validate input columns"""
        for column in REQUIRED_COLUMNS:
            if column.value not in columns:
                raise ValueError(f"CSV datasource is missing column '{column.value}'.")

        return columns

    def _enumerate_skip(self, s: str) -> str:
        """
        Replace 'skip' with skip1, skip2, ..., skipn.

        If the string doesn't match 'skip' precisely it is returned unchanged.
        """
        if s != "skip":
            return s

        self._skip_counter += 1
        return f"{s}{self._skip_counter}"

    def __init__(self, filename: os.PathLike | str, **kwargs) -> None:
        """
        CSV-files have to follow a somewhat strict syntax. Only commas are
        accepted as value separators and the following columns are all
        mandatory:

            station, t, x, y, z, sx, sy, sz

        where station is the station name, t a timestamp given in decimalyears,
        (x,y,z) are the spatial coordinates and (sx, sy, sz) are the corresponding
        standard deviation of those coordinates. Coordinate weights can be given
        in a column named weigth. If weights are not given they are set to 1.0.

        The column order can be changed by specifying `columns`. In case there
        are more columns than needed in the CSV-file, they can be skipped using
        the "skip" column-type.

        Parameters:
            filename:   The file to read
            columns:    A list of columns, in case the file has a column order
                        that differs from Transformo's default ordering.
        """
        super().__init__(filename=filename, **kwargs)

        # validate columns
        self._skip_counter = 0

        with open(self.filename, encoding="utf-8") as csvfile:
            has_header = csv.Sniffer().has_header(csvfile.read(1024))
            csvfile.seek(0)  # reset file handle

            columns = [self._enumerate_skip(c.value) for c in self.columns]

            # csv_reader = csv.reader(csvfile)
            csv_reader = csv.DictReader(csvfile, fieldnames=columns)

            if has_header:  # skip the header
                next(csv_reader, None)

            try:
                self.coordinates = [_dict_to_coordinate(row) for row in csv_reader]
            except TypeError as exception:
                raise ValueError(
                    f"Content of file doesn't match specified columns: {exception}"
                ) from exception
            except pydantic.ValidationError as exception:
                # if we get a ValidationError in the first row we've
                # probably met a header
                logger.error(exception)
                raise ValueError("CsvDataSource validation error") from exception

        for coordinate in self.coordinates:
            logger.info(coordinate)
