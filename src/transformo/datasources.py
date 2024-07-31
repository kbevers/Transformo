"""
Transformo reader classes.
"""

from __future__ import annotations

import csv
import os

import numpy as np
import pydantic

from transformo import Coordinate, TranformoReaderValidationError, logger
from transformo.protocols import DataSourceLike


class DataSource:
    """Base reader class."""

    coordinates: list[Coordinate] = []

    def __init__(self, coordinates: list[Coordinate] | None = None) -> None:
        """Set up base reader."""
        if coordinates is not None:
            self.coordinates = coordinates

    def __add__(self, other) -> DataSourceLike:
        """
        Add two datasources.

        Effectively the `coordinates` lists in the two `DataSource`s are joined together.
        The returned object is a generic `DataSource`, no matter what subclass of `DataSource`
        the two sources are created from.
        """
        return DataSource(coordinates=self.coordinates + other.coordinates)

    @property
    def coordinate_matrix(self) -> np.typing.ArrayLike:
        """"""
        return np.array([c.vector for c in self.coordinates])


class FileDataSource(DataSource):
    """Common DataSource for files."""

    filename: os.PathLike | str


class CsvDataSource(FileDataSource):
    """Reader for generic CSV-files."""

    def __init__(self, filename: os.PathLike | str) -> None:
        """
        CSV-files have to follow a strict syntax. Only commas are accepted as
        value separators and the following columns are all mandatory in the
        listed order:

            station, t, x, y, z, wx, wy, wz

        where station is the station name, t a timestamp given in decimalyears,
        (x,y,z) are the spatial coordinates and (wx, wy, wz) are the corresponding
        weighths of those coordinates.

        Parameters:
            csv_file:           The file to read
        """
        super().__init__()

        self.filename = filename

        with open(self.filename, encoding="utf-8") as csvfile:
            has_header = csv.Sniffer().has_header(csvfile.read(1024))
            csvfile.seek(0)  # reset file handle

            csv_reader = csv.reader(csvfile)

            if has_header:  # skip the header
                next(csv_reader, None)

            try:
                self.coordinates = [Coordinate.from_str(*row) for row in csv_reader]
            except pydantic.ValidationError as exception:
                # if we get a ValidationError in the first row we've
                # probably met a header
                logger.error(exception)
                raise TranformoReaderValidationError(
                    "CsvReader validation error"
                ) from exception

        for coordinate in self.coordinates:
            logger.info(coordinate)
