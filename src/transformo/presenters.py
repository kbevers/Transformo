"""
Transformo Presenter classes.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal, Protocol

import pydantic
from py_markdown_table.markdown_table import markdown_table

from transformo.datasources import DataSource, DataSourceLike
from transformo.operators import Operator, OperatorLike


def construct_markdown_table(header: list[str], rows: list[list[str]]) -> str:
    """
    Present data in tabular form using the Markdown format.

    The number of elements in the header must be equal to the number of
    elements in the individual rows.

    Data is expected as strings. Often numbers will be presented in a
    table. The responsibility of how data is formatted is left to the
    caller.

    Parameters:
        header: Titles for each column in the table
        rows:   Values of cells in table.
    """
    data = [dict(zip(header, row)) for row in rows]

    table = markdown_table(data)
    table.set_params(
        quote=False, padding_width=2, padding_weight="centerright", row_sep="markdown"
    )

    return table.get_markdown()


class PresenterLike(Protocol):
    """Protocal for Transformo Presenter classes."""

    type: Any

    def evaluate(
        self, operators: list[OperatorLike], results: list[DataSourceLike]
    ) -> None:
        """
        Store parsed information from operators and resulting datasources in
        internal data container for further processing.
        """


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
    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
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

    def as_markdown(self) -> str:
        """
        Present result in the markdown text format.
        """
        return "*This section intentionally left blank.*"


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

    def as_markdown(self) -> str:
        """Return PROJstring as text."""
        params = json.loads(self.as_json())
        txt = params["projstring"]
        formatted_projstring = txt.replace(" +step", "\n  +step").strip()

        markdown = f"""
Transformation parameters given as a [PROJ](https://proj.org/) string.
```
{formatted_projstring}
```
""".strip()

        return markdown


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
