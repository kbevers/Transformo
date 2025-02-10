"""
Core elements of Transformo.

These are the basic building blocks of the Transformo system.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal

import numpy as np
import pydantic
import pyproj

from transformo._typing import CoordinateMatrix, Vector
from transformo.datatypes import Coordinate, Parameter


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
    # when overriding settings etc.
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

    def __add__(self, other) -> DataSource:
        """
        Add two `DataSource`s.

        Effectively the `coordinates` lists in the two `DataSource`s are
        joined together. The returned object is a generic `DataSource`,
        no matter what subclass of `DataSource` the two sources are created from.
        """
        # new_coordinate_list = self.coordinates + other.coordinates
        # return DataSource(coordinates=new_coordinate_list)
        return CombinedDataSource(self, other)

    def __hash__(self) -> int:
        """
        Hash of the DataSource.

        Two identicial DataSources will return different hashes. E.g., it is
        possible to instantiate two DataSources based on the same file without
        them having the same hash.
        """
        return hash(str(id(self)))

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

    @property
    def stations(self) -> list[str]:
        """
        Get list of stations.
        """
        return [c.station for c in self.coordinates]  # pylint: disable=E1133

    @property
    def origins(self) -> list[DataSource]:
        """
        Get a list of this DataSource's origins.
        """
        return [self]

    def update_coordinates(self, coordinates: CoordinateMatrix) -> DataSource:
        """
        Create a new DataSource based on the current instance but with the
        coordinates updated to those in `coordinates`.
        """
        old_coordinates: list[Coordinate] = self.coordinates
        if len(old_coordinates) != coordinates.shape[0]:
            raise ValueError("Incorrect number of coordinates!")

        new_coordinates: list[Coordinate] = []
        for i, coord in enumerate(old_coordinates):
            coord = Coordinate(
                station=coord.station,
                t=coord.t,
                x=coordinates[i, 0],
                y=coordinates[i, 1],
                z=coordinates[i, 2],
                sx=coord.sx,
                sy=coord.sy,
                sz=coord.sz,
                w=coord.w,
            )
            new_coordinates.append(coord)

        return DataSource(coordinates=new_coordinates)


class CombinedDataSource(DataSource):
    """Combination of two or more DataSource's."""

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "combined_datasource"
    else:
        type: Literal["combined_datasource"] = "combined_datasource"

    def __init__(self, first: DataSource, second: DataSource, **kwargs) -> None:
        """Set up base reader."""
        coordinates = first.coordinates + second.coordinates
        super().__init__(coordinates=coordinates, **kwargs)

        self._origins: list[DataSource] = [first, second]

    @property
    def origins(self) -> list[DataSource]:
        l = []
        for datasource in self._origins:
            l.extend(datasource.origins)

        # we do not want to return duplicates
        return list(set(l))


class Operator(pydantic.BaseModel):
    """
    Base Operator class.

    Operators are essential building blocks for the Pipeline. All operators
    have the ability to manipulate coordinates, generally in the sense of a geodetic
    transformation. In addition operators *can* implement a method to derive
    parameters for said coordinate operation. Most Operators do, but not all.

    So, Operators have two principal modes of operation:

        1. Coordinate operations, as defined in the ISO 19111 terminology
        2. Estimating parameters for the coordinate operations

    The abilities of a Operator are determined by the methods that enheriting classes
    implement. *All* Operator's must implement the `forward` method and they *can*
    implement the `estimate` and `inverse` methods. If only the `forward` method is
    implemented the operator will exist as a coordinate operation that can't
    estimate parameters.
    """

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "operator"
    else:
        type: Literal["operator"] = "operator"

    # User-specified name of the Operator, for easy referencing
    # when overriding settings etc.
    name: str | None = None

    def __init__(
        self,
        name: str | None = None,
        **kwargs,
    ) -> None:
        """Set up base operator."""
        super().__init__(name=name, **kwargs)

        self._transformation_parameters_given: bool = False

    def __repr__(self) -> str:
        """ """
        params = ", ".join(f"{p.name}: {p.value}" for p in self.parameters)
        return self.__class__.__name__ + f"({params})"

    @classmethod
    def get_subclasses(cls) -> Iterable[type[Operator]]:
        """
        Return a tuple of all known subclasses to `Operator`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the Pipeline class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "operator" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [Operator] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @abstractmethod
    def _proj_name(self) -> str:
        """Helper for the `proj_operation_name` property."""

    @abstractmethod
    def _parameter_list(self) -> list[Parameter]:
        """Helper for the `parameters` property."""

    @property
    def can_estimate(self) -> bool:
        """
        Determine if an `Operator` is able to estimate parameters or not.

        An operator can be unfit for estimating parameters in two ways:

            1. The `estimate()` method is not implemented
        or
            2. The `Operator` was invoked with parameters that would otherwise
               need to be estimated

        In the last case the operator will only be used to convert coordinates
        using the `forward()` method of the `Operator`.
        """
        if self._transformation_parameters_given:
            return False

        # If we get to here, no parameters were supplied by the user and
        # we are expected to estimate them. We don't want to spend to much
        # energy on this, so simple coordinate and weight matrices are
        # given as input. If `estimate()` is implemented *some* parameters
        # will be estimated and stored in the `Operator` but they will be
        # discarded when `estimate()` is executed again with proper input.
        zero_matrix = np.zeros(shape=(4, 3))
        try:
            self.estimate(zero_matrix, zero_matrix, zero_matrix, zero_matrix)
        except NotImplementedError:
            return False

        return True

    @property
    def proj_operation_name(self) -> str:
        """
        Return the name of the PROJ operation that relates to
        the Transformo Operator.
        """
        return self._proj_name()

    @property
    def parameters(self) -> list[Parameter]:
        """
        Return parameters in a standardized way.

        Parameters are returned as a list of `Parameters`. All Parameters are named
        and their value is optional. Parameters are generally meant to be equivalent
        to parameters in PROJ.

        Following PROJ conventions, a parameter entry be on one of the following
        forms:

            1. param=number
            2. param=string
            3. param

        Abstract method. Needs to be implemented by inheriting classes.
        """
        return self._parameter_list()

    @abstractmethod
    def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Forward method of the Operator.

        Abstract. Needs to be implemented by inheriting classes.
        """

    def inverse(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Inverse method of the Operator.

        Abstract. Can be implemented by inheriting classes.
        """
        raise NotImplementedError

    def estimate(
        self,
        source_coordinates: CoordinateMatrix,
        target_coordinates: CoordinateMatrix,
        source_weights: CoordinateMatrix,
        target_weights: CoordinateMatrix,
    ) -> None:
        """
        Estimate parameters.

        Abstract. Can be implemented by inheriting classes.
        """
        raise NotImplementedError


class Presenter(pydantic.BaseModel):
    """Base Presenter class."""

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "presenter"
    else:
        type: Literal["presenter"] = "presenter"

    # User-specified name of the Presenter, for easy referencing
    # when overriding settings etc.
    name: str | None = None

    def __init__(
        self,
        name: str | None = None,
        **kwargs,
    ) -> None:
        """Set up base presenter."""
        super().__init__(name=name, **kwargs)

    @classmethod
    def get_subclasses(cls) -> Iterable[type[Presenter]]:
        """
        Return a tuple of all known subclasses to `Presenter`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the `Pipeline` class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "presenter" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [Presenter] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @abstractmethod
    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        """
        Evaluate information from operators and resulting datasources and store in
        internal data container for use in program output.
        """

    @abstractmethod
    def as_json(self) -> str:
        """
        Present results as JSON.
        """

    @abstractmethod
    def as_markdown(self) -> str:
        """
        Present result in the Markdown text format.
        """

    @property
    def presenter_name(self) -> str:
        """Name of the Presenter"""
        if self.name:
            return self.name

        return self.type


class Transformer:
    """
    Transform coordinates using PROJ.

    Interface for pyproj that works using Transformo's datatypes such
    as CoordinateMatrix and Vector.
    """

    def __init__(self, transformer: pyproj.Transformer | None = None):
        """
        Initialize a Transformer.

        If None is passed to the method a generic "noop" PROJ transformation
        is created.

        Generally advised to instantiate `Transformer`s using class methods
        such as `from_projstring`.
        """
        if not transformer:
            self.transformer = pyproj.Transformer.from_pipeline("+proj=noop")
        else:
            self.transformer = transformer

    @classmethod
    def from_projstring(cls, projstring: str):
        """
        Instantiate a `Transformer` using a PROJ string.

        Any valid PROJ string can be used.
        """
        transformer = pyproj.Transformer.from_pipeline(projstring)
        return Transformer(transformer=transformer)

    def transform_many(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
        """
        Transform a CoordinateMatrix.
        """
        results = self.transformer.itransform(coordinates)
        return np.array(list(results))

    def transform_one(self, coordinate: Vector) -> Vector:
        """
        Transform a single coordinate.
        """
        (x, y, z) = self.transformer.transform(
            xx=coordinate[0], yy=coordinate[1], zz=coordinate[2]
        )

        return np.array((x, y, z))
