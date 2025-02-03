"""
DataSources for files created by the Bernese software.

References:
- Bernese 5.2 manual, section 24.7.1 "Station Coordinates".

"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from transformo.core import DataSource
from transformo.datatypes import Coordinate


def datetime_to_decimal_year(date_time: datetime) -> float:
    """
    Convert a datetime object to a decimal year.
    """
    year = date_time.year
    start_of_year = datetime(year, 1, 1)
    start_of_next_year = datetime(year + 1, 1, 1)

    days_in_year = (start_of_next_year - start_of_year).days

    days_passed = (date_time - start_of_year).days
    seconds_passed = (date_time - start_of_year).seconds

    fraction_of_year = days_passed / days_in_year + seconds_passed / (
        days_in_year * 24 * 60 * 60
    )

    return year + fraction_of_year


@dataclass
class CrdCoordinate:
    """Datastructure for coordinates from a CRD-file"""

    station: str
    flag: str | None
    x: float
    y: float
    z: float


def crd_line_to_coordinate(line: str) -> CrdCoordinate:
    """
    Parse lines in a CRD-file.

    Below are examples lines:

      2  BUDD 10101S001    3513649.04104   778955.02287  5248202.12784    A
      2  BUDD 10101S001    3513649.04138   778955.02303  5248202.12838    A      GRE
      5  ESBH 10115M002    3585278.72001   531971.41288  5230646.6845
    920  KELY              1575559.29890 -1941827.91620  5848076.48160    A

    Raises:
        ValueError:     If the function can't make sense of the input string
    """
    flag = None
    split_line = line.split()
    match len(split_line):
        case 5:
            (_, station, x, y, z) = split_line
        case 6:
            (_, station, x, y, z, flag) = split_line
            try:
                float(x)
            except ValueError:
                # It is possible to have a line with station+antenna and no flag,
                # which result in data in 6 columns. We check if third can be
                # converted to a float. If not, there's something in the antenna
                # column and we parse the columns differently:
                (_, station, _, x, y, z) = split_line
                flag = None
        case 7:
            (_, station, _, x, y, z, flag) = split_line
        case 8:
            (_, station, _, x, y, z, flag, _) = split_line
        case _:
            raise ValueError

    return CrdCoordinate(station, flag, float(x), float(y), float(z))


class BerneseCrdDataSource(DataSource):
    """
    Parse data from a Bernese CRD-file.

    CRD-files do not have any information about the uncertainties of the
    coordinates. A file-wide uncertainty can be set using the field "stddev".
    If "stddev" is not set the value 0.0 is used.

    Weights aren't specified in the file either and are set to 1.0 for all
    coordinates in the file.

    Each coordinate has a flag attached to it, most commonly seen are "A" or
    "W" that specifies if a station has been constrained (W) or not (A) in
    the coordinate solution. A list of flags to discard can be given.
    """

    type: Literal["bernese_crd"] = "bernese_crd"
    filename: os.PathLike | str
    stddev: float = 0.0
    weight: float = 1.0
    discard_flags: list[str] | None = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # The overall structure of a CRD-file is:
        #
        #     1. Header
        #     2. Coordinate table
        #     3. Footer
        #
        # There is seemingly no fixed structure to these files. The header can differ
        # slightly from file to file. The coordinate table is made up of somewhere
        # between 6 and 8 columns. The footer is not always present. In the code
        # trys it's best to parse the available information without imposing a too
        # strict understanding of the file's structure.
        with open(self.filename, "r", encoding="utf-8") as crdfile:
            lines = crdfile.readlines()

        if not self.discard_flags:
            self.discard_flags = []

        coordinate_epoch = None
        for line in lines:
            # The epoch is located somewhere at the top of the file. Usually at line
            # 2 or 3. We try parsing it until successful
            if not coordinate_epoch:
                try:
                    # epoch seems to be a fixed placement in the line
                    epoch_datetime = datetime.strptime(line[47:66], "%Y-%m-%d %H:%M:%S")
                    coordinate_epoch = datetime_to_decimal_year(epoch_datetime)
                except ValueError:
                    pass

            # After the epoch line parsed we encounter a few lines that are either
            # empty or a table header. We try to read everything as a cooordinate
            # and continue to the next line upon failure. This works until the end
            # of the file is reached.
            try:
                crd_coord = crd_line_to_coordinate(line)
            except ValueError:
                continue

            if crd_coord.flag in self.discard_flags:
                continue

            self.coordinates.append(
                Coordinate(
                    crd_coord.station,
                    t=coordinate_epoch,
                    x=crd_coord.x,
                    y=crd_coord.y,
                    z=crd_coord.z,
                    sx=1.0,
                    sy=1.0,
                    sz=1.0,
                    w=1.0,
                )
            )
