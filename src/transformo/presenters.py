"""
Transformo Presenter classes.
"""

from __future__ import annotations

import json
import textwrap
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal, Protocol

import pydantic

from transformo import Coordinate
from transformo.datasources import DataSource, DataSourceLike
from transformo.operators import Operator, OperatorLike


class PresenterLike(Protocol):
    """Protocal for Transformo Presenter classes."""

    type: Any

    def evaluate(
        self, operators: list[OperatorLike], results: list[DataSourceLike]
    ) -> None:
        """
        Parse information from operators and result datasources and store in
        internal data container for further processing.
        """


class Presenter(pydantic.BaseModel):
    """Base Result class."""

    # Mypy and pydantic have conflicting needs:
    # Pydantic won't work unless the type is a stric Literal
    # and MyPy will complain about conflicting types when the base class
    # is using a different Literal than an inheriting class.
    if TYPE_CHECKING:
        type: Any = "presenter"
    else:
        type: Literal["presenter"] = "presenter"

    # User-specified name of the Presenter, for easy referencing
    # when overriding settings
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
        Return a tuple of all known subclasses to `Result`.

        This classmethod supports pydantic in dynamically creating a valid model
        for the Pipeline class when serialising the pipeline from an external
        configuration file.
        """
        # the parent class "result" is needed in the list as well, since
        # DataSource's can be instantiated as well as classes inheriting from it
        subclasses = [Presenter] + list(cls.__subclasses__())

        # we want to find all levels of subclasses, not just the first level
        for subclass in cls.__subclasses__():
            subclasses.extend(subclass.get_subclasses())

        return tuple(set(subclasses))

    @abstractmethod
    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Evalute information from operators and result datasources and store in
        internal data container for use in program output.
        """

    @abstractmethod
    def as_json(self) -> str:
        """
        Present results as JSON.
        """

    @abstractmethod
    def as_text(self) -> str:
        """
        Present result in text format.
        """


class DummyPresenter(Presenter):
    """
    A presenter that doesn't do much...
    """

    type: Literal["dummy_presenter"] = "dummy_presenter"

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Evaluate `results` created by `operators`.
        """

    def as_json(self) -> str:
        """
        Present results as JSON.
        """
        return "{}"

    def as_text(self) -> str:
        """
        Present result in text format.
        """
        return ""


class PROJPresenter(Presenter):
    """
    Present parameters as a PROJ string.

    Possible future usefull settings:
        - Number of decimal places for floats.
    """

    type: Literal["proj_presenter"] = "proj_presenter"

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._output: dict[str, str] = {}

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Parse parameters from `operators`.

        Ignores contents of `results`.
        """
        steps = []
        for operator in operators:
            if operator.proj_operation_name == "noop":
                continue

            projstr = f"+proj={operator.proj_operation_name}"
            for param, value in operator.parameters.items():
                if value is None:
                    projstr += f" +{param}"
                else:
                    projstr += f" +{param}={value}"

            steps.append(projstr)

        if len(steps) == 0:
            self._output["projstring"] = "+proj=noop"
            return

        if len(steps) == 1:
            self._output["projstring"] = steps[0]
            return

        self._output["projstring"] = "+proj=pipeline +step " + " +step ".join(steps)

    def as_json(self) -> str:
        """
        Return PROJstring as a JSON string.

        Use the key "projstring" to access the PROJstring.
        """
        return json.dumps(self._output)

    def as_text(self) -> str:
        """Return PROJstring as text."""
        params = json.loads(self.as_json())
        txt = params["projstring"]
        return txt.replace(" +step", "\n  +step").strip()


class CoordinatePresenter(Presenter):
    """
    Present coordinates for all stages of a pipeline.

    Possible future useful settings:
        - Include timestamps

    """

    type: Literal["coordinate_presenter"] = "coordinate_presenter"

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._operator_titles: list[str] = []
        self._steps: list[dict[str, list[float]]] = []

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Parse coordinates from `results`.

        Ignores contents of `operators`.

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
                data[c.station] = [c.x, c.y, c.z]
            steps.append(data)

        self._steps = steps

        operator_titles = []
        for operator in operators:
            operator_titles.append(repr(operator))

        self._operator_titles = operator_titles

    def as_json(self) -> str:
        return json.dumps(self._steps)

    def as_text(self) -> str:
        fmt = ">14.5f"

        txt = ""
        for i, step in enumerate(self._steps):
            if i == 0:
                stepname = "Source coordinates"
            elif i < len(self._steps) - 1:
                stepname = f"Step {i}: {self._operator_titles[i-1]}"
            else:
                stepname = "Target coordinates"

            txt += "=" * 51 + "\n"
            txt += f"# {stepname}\n"
            txt += "=" * 51 + "\n"
            for station, c in step.items():
                x = format(c[0], fmt)
                y = format(c[1], fmt)
                z = format(c[2], fmt)
                txt += f"{station:<6} {x} {y} {z}\n"

            txt += "\n"

        return txt.strip()
