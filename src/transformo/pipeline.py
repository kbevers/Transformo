"""
Transformo pipeline classes.
"""

from __future__ import annotations

import textwrap
from typing import Annotated, Union

import pydantic
import pydantic_yaml

from transformo import TransformoError
from transformo.datasources import DataSource, DataSourceLike
from transformo.operators import Operator, OperatorLike
from transformo.presenters import Presenter, PresenterLike
from transformo.typing import CoordinateMatrix


class TransformoPipeline(pydantic.BaseModel):
    """The backbone of Transformo"""

    source_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    target_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    operators: list[Annotated[Union[Operator.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    presenters: list[Annotated[Union[Presenter.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]

    def __init__(
        self,
        source_data: list[DataSourceLike],
        target_data: list[DataSourceLike],
        operators: list[OperatorLike],
        presenters: list[PresenterLike],
    ) -> None:
        """Set up for pipelines"""
        super().__init__(
            source_data=source_data,
            target_data=target_data,
            operators=operators,
            presenters=presenters,
        )

        def combine_datasources(sources=list[DataSource]) -> DataSource:
            combined_datasource = sources[0]
            for source in sources[1:]:
                combined_datasource += source
            return combined_datasource

        # set up combined datasources for both source and target data
        self._combined_source_data = combine_datasources(self.source_data)
        self._combined_target_data = combine_datasources(self.target_data)

        self._intermediate_results: list[DataSource] = [self._combined_source_data]

    @classmethod
    def from_json(cls, json: str | bytes | bytearray) -> TransformoPipeline:
        """
        Serialize a pipeline from JSON.
        """
        return cls.model_validate_json(json)

    @classmethod
    def from_yaml(cls, yaml: str | bytes | bytearray) -> TransformoPipeline:
        """
        Serialize a pipeline from YAML.
        """
        return pydantic_yaml.parse_yaml_raw_as(cls, yaml)

    def to_json(self) -> str:
        """
        Return the pipeline setup as JSON.
        """
        return self.model_dump_json(indent=2)

    def to_yaml(self) -> str:
        """
        Return the pipeline setup as YAML.
        """
        return pydantic_yaml.to_yaml_str(self)

    @property
    def all_source_data(self) -> DataSource:
        """
        A combination of all source DataSource's.
        """
        return self._combined_source_data

    @property
    def all_target_data(self) -> DataSource:
        """
        A combination of all target DataSource's.
        """
        return self._combined_target_data

    @property
    def results(self) -> list[DataSource]:
        """
        ...
        """
        if len(self._intermediate_results) != len(self.operators) + 2:
            raise TransformoError("Pipeline has not been processed yet")
        return self._intermediate_results

    @property
    def source_coordinates(self) -> CoordinateMatrix:
        """
        The combined set of source coordinates.
        """
        combined_datasource = self.source_data[0]
        for datasource in self.source_data[1:]:
            combined_datasource += datasource

        return combined_datasource.coordinate_matrix

    @property
    def target_coordinates(self) -> CoordinateMatrix:
        """
        The combined set of target coordinates.
        """
        combined_datasource = self.target_data[0]
        for datasource in self.target_data[1:]:
            combined_datasource += datasource

        return combined_datasource.coordinate_matrix

    def process(self) -> None:
        """
        Process all `Operator`s in the pipeline and pass the results to the
        `Presenter`s for evaluation.
        """
        current_step_coordinates = self.source_coordinates
        for operator in self.operators:
            if operator.can_estimate:
                operator.estimate(
                    current_step_coordinates,
                    self.target_coordinates,
                    # TODO: Handle weights
                    None,
                    None,
                )
            current_step_coordinates = operator.forward(current_step_coordinates)
            current_step_datasource = self.all_source_data.update_coordinates(
                current_step_coordinates
            )
            self._intermediate_results.append(current_step_datasource)

        self._intermediate_results.append(self._combined_target_data)

        for presenter in self.presenters:
            presenter.evaluate(operators=self.operators, results=self.results)

    def results_as_text(self) -> str:
        """
        Return the results from the pipeline in clear text format,
        as specified with the given `Presenter`s.
        """
        text = ""
        for presenter in self.presenters:

            title = repr(presenter)
            body = textwrap.indent(presenter.as_text(), prefix="  ")

            text += f"{title}\n\n"
            text += f"{body}\n\n"

        return text

    def results_as_json(self) -> str:
        """
        Return the results from the pipeline in JSON format,
        as specified with the given `Presenter`s.
        """
        return "{}"

    def results_as_html(self) -> str:
        """
        Return the results from the pipeline in HTML format,
        as specified with the given `Presenter`s.

        """
        return "<html><title>Transformo Results<title><body></body></html>"
