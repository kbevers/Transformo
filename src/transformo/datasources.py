"""
Transformo reader classes.
"""

from __future__ import annotations

import csv
import os
from typing import TYPE_CHECKING, Any, Iterable, Literal

import numpy as np
import pydantic

from transformo import Coordinate, TranformoReaderValidationError, logger
from transformo.protocols import CoordinateMatrix, DataSourceLike


class DataSource(pydantic.BaseModel):
    """Base class for any Transformo data source."""

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "datasource"
    else:
        type: Literal["datasource"] = "datasource"

    # User-specified name of the DataSource, for easy referencing
    # when overriding settings
    name: str | None = None

    # coordinates are not included in pipeline serialization
    coordinates: list[Coordinate] = pydantic.Field(default_factory=list, exclude=True)

    def __init__(
        self,
        coordinates: list[Coordinate] | None = None,
        name: str | None = None,
        **kwargs,
    ) -> None:
        """Set up base reader."""
        if coordinates is None:
            # it's not kosher to initialize a value with [] as default
            coordinates = []

        super().__init__(coordinates=coordinates, name=name, **kwargs)

    def __add__(self, other) -> DataSourceLike:
        """
        Add two `DataSource`s.

        Effectively the `coordinates` lists in the two `DataSource`s are joined together.
        The returned object is a generic `DataSource`, no matter what subclass of `DataSource`
        the two sources are created from.
        """
        new_coordinate_list = self.coordinates + other.coordinates
        return DataSource(coordinates=new_coordinate_list)

    @classmethod
    def get_subclasses(cls) -> Iterable[type[DataSource]]:
        """
        Return a tuple of all known subclasses to `DataSource`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the Pipeline class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "datasource" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [DataSource] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @property
    def coordinate_matrix(self) -> CoordinateMatrix:
        """
        The coordinates in matrix form.
        """
        # Understably, pylint doesn't recognize pydantic.Field as an Iteralble
        return np.array(
            [c.vector for c in self.coordinates]  # pylint: disable=not-an-iterable
        )


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
                raise TranformoReaderValidationError(
                    "CsvDataSource validation error"
                ) from exception

        for coordinate in self.coordinates:
            logger.info(coordinate)


class BerneseCrdDataSource(DataSource):
    """Parse data from a Bernese CRD-file."""

    type: Literal["bernese_crd"] = "bernese_crd"
    filename: os.PathLike | str

    def __init__(self, filename: os.PathLike | str, **kwargs) -> None:
        raise NotImplementedError
