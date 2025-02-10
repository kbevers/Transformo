"""
Transformo pipeline classes.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Union

import pydantic
import pydantic_yaml

import transformo

# We need the subclassed DataSources, Operators and Presenters to be known to Pydantic
# in order to resolve the type-discriminator. Without importing them, Python doesn't
# know about the subclasses and they aren't exposed in __subclasses__.
import transformo.datasources
import transformo.operators
import transformo.presenters
from transformo._typing import (
    CoordinateMatrix,
    DataSourceLike,
    OperatorLike,
    PresenterLike,
)
from transformo.core import DataSource, Operator, Presenter


class Pipeline(pydantic.BaseModel):
    """The backbone of Transformo"""

    source_data: list[  # type: ignore[valid-type]
        Annotated[
            Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")
        ]
    ]
    target_data: list[  # type: ignore[valid-type]
        Annotated[
            Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")
        ]
    ]
    operators: list[  # type: ignore[valid-type]
        Annotated[
            Union[Operator.get_subclasses()], pydantic.Field(discriminator="type")
        ]
    ]
    presenters: list[  # type: ignore[valid-type]
        Annotated[
            Union[Presenter.get_subclasses()], pydantic.Field(discriminator="type")
        ]
    ]

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

        # set up combined datasources for both source and target data
        self._combined_source_data = sum(self.source_data, DataSource(None))
        self._combined_target_data = sum(self.target_data, DataSource(None))

        self._intermediate_results: list[DataSource] = []

    @classmethod
    def from_yaml(cls, yaml: str | bytes | bytearray) -> Pipeline:
        """
        Serialize a pipeline from YAML.
        """
        return pydantic_yaml.parse_yaml_raw_as(cls, yaml)

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
        Return coordinate results, including intermediate steps.

        If the pipeline hasn't been processed before calling this method,
        it will be done before returning the results.

        TODO: Think of a better name.
        """
        if len(self._intermediate_results) != len(self.operators):
            self.process()
        return self._intermediate_results

    @property
    def source_coordinates(self) -> CoordinateMatrix:
        """
        The combined set of source coordinates in matrix form.
        """
        combined_datasource = self.source_data[0]
        for datasource in self.source_data[1:]:
            combined_datasource += datasource

        return combined_datasource.coordinate_matrix

    @property
    def target_coordinates(self) -> CoordinateMatrix:
        """
        The combined set of target coordinates in matrix form.
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

        for presenter in self.presenters:
            presenter.evaluate(
                operators=self.operators,
                source_data=self.all_source_data,
                target_data=self.all_target_data,
                results=self.results,
            )

    def results_as_markdown(self) -> str:
        """
        Return the results from the pipeline in markdown format,
        as specified with the given `Presenter`s.
        """
        text = f"""
# Transformo Results
*Created with Transformo version {transformo.__version__}, {datetime.now()}*.\n
""".lstrip()

        for presenter in self.presenters:
            section_header = presenter.presenter_name
            body = presenter.as_markdown()

            text += f"## {section_header}\n\n"
            text += f"{body}\n\n"

        return text.rstrip()

    def results_as_json(self) -> str:
        """
        Return the results from the pipeline in JSON format,
        as specified with the given `Presenter`s.

        Each `Presenter`
        """
        # There's a bit of back and forth between JSON representations here. It's
        # not particularly efficient but it is easy and it allows the individual
        # presentations to return a JSON string outside the context of a `Pipeline`.
        data = {p.presenter_name: json.loads(p.as_json()) for p in self.presenters}
        return json.dumps(data)
