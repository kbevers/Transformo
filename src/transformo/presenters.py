"""
Transformo Presenter classes.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Iterable, Literal

import pydantic

from transformo.datasources import DataSource
from transformo.operators import Operator


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
    def parse_results(
        self, operators: list[Operator], results: list[DataSource]
    ) -> None:
        """
        Parse information from operators and result datasources and store in
        internal data container for further processing.
        """

    @abstractmethod
    def as_json(self) -> str:
        """
        Present results as JSON.
        """


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

    def parse_results(
        self, operators: list[Operator], results: list[DataSource]
    ) -> None:
        """
        Parse parameters from `operators`.

        Ignores contents of `results`.
        """
        if len(operators) == 0:
            self._output["projstring"] = "+proj=noop"
            return

        projstr = ""
        if len(operators) > 1:
            projstr = "+proj=pipeline"

        for operator in operators:
            if len(operators) > 1:
                projstr += " +step "

            projstr += f"+proj={operator.proj_operation_name}"

            for param, value in operator.parameters.items():
                if value is None:
                    projstr += f" +{param}"
                else:
                    projstr += f" +{param}={value}"

        self._output["projstring"] = projstr

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
        return txt.replace(" +step", "\n  +step")
