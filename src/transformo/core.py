"""
Core elements of Transformo.

These are the basic building blocks of the Transformo system.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal

import numpy as np
import pydantic

from transformo._typing import CoordinateMatrix
from transformo.datatypes import Coordinate, Parameter


@pydantic.dataclasses.dataclass()
class CoordinateOverrides:
    """
    Helper dataclass, that enables overriding coordinate values in a DataSource.

    The fields in this class are the same as the fields of Coordinate, with the
    exception that none of the fields are required and their default values are
    set to None.

    If the definitions are changed here, they need to be changed in Coordinate
    as well.
    """

    # station name
    station: str | None = pydantic.Field(None, pattern="[A-z0-9].*", strict=True)

    # spatial coordinate elements
    x: float | None = pydantic.Field(None, allow_inf_nan=False, strict=True)
    y: float | None = pydantic.Field(None, allow_inf_nan=False, strict=True)
    z: float | None = pydantic.Field(None, allow_inf_nan=False, strict=True)

    sx: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)
    sy: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)
    sz: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)

    # coordinate weight
    w: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)

    # coordinate epoch
    t: float | None = pydantic.Field(
        None, ge=0.0, le=10000.0, allow_inf_nan=False, strict=True
    )


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

    # standard deviations, uncertainties
    sx: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)
    sy: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)
    sz: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)

    # coordinate weight
    w: float | None = pydantic.Field(None, ge=0.0, allow_inf_nan=False, strict=True)

    # coordinate epoch
    t: float | None = pydantic.Field(
        None, ge=0.0, le=10000.0, allow_inf_nan=False, strict=True
    )

    # station-based overrides
    overrides: dict[str, CoordinateOverrides] | None = pydantic.Field(
        default_factory=dict.__call__
    )

    # coordinates are not included in pipeline serialization
    coordinates: list[Coordinate] = pydantic.Field(default_factory=list, exclude=True)

    def __init__(
        self,
        name: str | None = None,
        coordinates: list[Coordinate] | None = None,
        overrides: dict[str, CoordinateOverrides] | None = None,
        **kwargs,
    ) -> None:
        """Set up base reader."""
        if coordinates is None:
            # it's not kosher to initialize a value with [] as default
            coordinates = []

        if overrides is None:
            overrides = {}

        super().__init__(
            name=name, coordinates=coordinates, overrides=overrides, **kwargs
        )

        # See the comment below regarding post initialization.
        # Execute post initialization if, and only if, self is a DataSource.
        #
        # pylint: disable=unidiomatic-typecheck - for once this is what is needed
        if type(self) is DataSource:
            self.__post_init__()

    # POST INITIALIZATION
    #
    # Implement a post init method, that is run once after the pydantic model
    # has been serialized AND __init__() of subclasses of DataSource has been
    # processed. This fascilitates the mechanism of overriding certain
    # coordinate values across a DataSource.
    #
    # The overrides works by using __init_subclass__() to set a decorator on
    # __init__(). That decorator is defined in __post_init__(). At first, this
    # might seem like an over-complication that would be solved by using
    # Pydantic's model_post_init() method the BaseModel. Unfortunately that is
    # processed as a final step of BaseModel.__init__(), which poses a problem
    # when a DataSource child is calling super().__init__() in order to
    # serialize the model.
    #
    # Note that this ONLY works on subclasses of a DataSource. To run the post
    # initialization on a DataSource that is not subclassed, a bit of extra
    # trickery is needed. See the final lines of DataSource.__init__() above.

    def __init_subclass__(cls, **kwargs):

        def init_decorator(previous_init):
            def new_init(self, *args, **kwargs):
                previous_init(self, *args, **kwargs)
                if isinstance(self, cls):
                    self.__post_init__()

            return new_init

        cls.__init__ = init_decorator(cls.__init__)

    def __post_init__(self) -> None:
        """
        Modify DataSource after the initial creation.

        This allow overrides of the original data, for instance by setting
        a different standard deviation of the coordinates in the DataSource.

        Additionally, station-based overrides are handled here.

        Do not override this method without calling super().__post_init__().
        Or better yet, do not override it at all.
        """
        # pylint: disable=unsubscriptable-object

        for c in self.coordinates:
            if self.sx is not None:
                c.sx = self.sx

            if self.sy is not None:
                c.sy = self.sy

            if self.sz is not None:
                c.sz = self.sz

            if self.w is not None:
                c.w = self.w

            if self.t is not None:
                c.t = self.t

            if self.overrides is None:
                continue

            if c.station in self.overrides.keys():
                # We store the original station name in key to avoid KeyError's
                # when overriding the station name. If c.station is used as the
                # key it will be overwritten in case a station is renamed in the
                # overrides.
                key = c.station

                # The use of the walrus operator here might look a bit
                # unnecessary, but it avoids a mypy incompatible type error
                if (station := self.overrides[key].station) is not None:
                    c.station = station

                if (x := self.overrides[key].x) is not None:
                    c.x = x

                if (y := self.overrides[key].y) is not None:
                    c.y = y

                if (z := self.overrides[key].z) is not None:
                    c.z = z

                if (sx := self.overrides[key].sx) is not None:
                    c.sx = sx

                if (sy := self.overrides[key].sy) is not None:
                    c.sy = sy

                if (sz := self.overrides[key].sz) is not None:
                    c.sz = sz

                if (w := self.overrides[key].w) is not None:
                    c.w = w

                if (t := self.overrides[key].t) is not None:
                    c.t = t

            self.coordinates = sorted(self.coordinates, key=lambda c: c.station)

    def __add__(self, other: DataSource) -> DataSource:
        """
        Add two `DataSource`s.

        Effectively the `coordinates` lists in the two `DataSource`s are
        joined together. The returned object is a generic `DataSource`,
        no matter what subclass of `DataSource` the two sources are created from.
        """
        # if either of the two DataSource's are empty there's no need to add them
        if not other.coordinates and self.coordinates:
            return self

        if not self.coordinates and other.coordinates:
            return other

        # if both are empty a single empty DataSource is returned
        if not self.coordinates and not other.coordinates:
            return DataSource(None)

        # at this point both DataSources contain valid data and we can combine them
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
    def weights_matrix(self) -> CoordinateMatrix:
        """
        A matrix of weights for each of the coordinate elements.

        Weights are determined based on the coordinate uncertainties and the
        station weights given in the DataSource. It is a combined weight, so to speak.

        The coordinate uncertainties are assumed to be standard deviations. The
        combined weights in the matrix are determined by

            weight = (1 / stddev**2) * station_weight
        """
        return np.array(
            [c.weights for c in self.coordinates]  # pylint: disable=not-an-iterable
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

    def station_union(self, other: DataSource) -> list[str]:
        return list(set(self.stations) & set(other.stations))

    def limit_to_stations(self, stations: list[str]) -> None:
        """
        Limit DataSource to stations given in supplied list.
        """
        stations_to_remove = []

        for c in self.coordinates:
            if c.station not in stations:
                stations_to_remove.append(c)

        for c in stations_to_remove:
            self.coordinates.remove(c)


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
        # we are expected to estimate them. We can only do that if the
        # operator has overloaded the `Operator.estimate` method.
        if type(self).estimate == Operator.estimate:
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
