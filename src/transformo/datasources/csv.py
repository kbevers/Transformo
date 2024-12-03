"""
The CSV DataSource for Transformo.
"""

import csv
import os
from typing import Literal

import pydantic

from transformo import logger
from transformo.core import DataSource
from transformo.datatypes import Coordinate


class CsvDataSource(DataSource):
    """Reader for generic CSV-files."""

    type: Literal["csv"] = "csv"
    filename: os.PathLike | str

    def __init__(self, filename: os.PathLike | str, **kwargs) -> None:
        """
        CSV-files have to follow a strict syntax. Only commas are accepted as
        value separators and the following columns are all mandatory in the
        listed order:

            station, t, x, y, z, sx, sy, sz, w

        where station is the station name, t a timestamp given in decimalyears,
        (x,y,z) are the spatial coordinates and (wx, wy, wz) are the corresponding
        weighths of those coordinates.

        Parameters:
            filename:   The file to read
        """
        super().__init__(filename=filename, **kwargs)

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
                raise ValueError("CsvDataSource validation error") from exception

        for coordinate in self.coordinates:
            logger.info(coordinate)
