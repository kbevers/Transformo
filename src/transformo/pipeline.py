"""
Transformo pipeline classes.
"""

from __future__ import annotations

from typing import Annotated, Union

import numpy as np
import pydantic
import pydantic_yaml

from transformo.datasources import DataSource
from transformo.estimators import Operator
from transformo.protocols import CoordinateMatrix, DataSourceLike, OperatorLike


class TransformoPipeline(pydantic.BaseModel):
    """The backbone of Transformo"""

    source_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    target_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    operators: list[Annotated[Union[Operator.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]

    def __init__(
        self,
        source_data: list[DataSourceLike],
        target_data: list[DataSourceLike],
        operators: list[OperatorLike],
    ) -> None:
        """Set up for pipelines"""
        super().__init__(
            source_data=source_data, target_data=target_data, operators=operators
        )

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
        Process all operators in the pipeline.
        """
        for operator in self.operators:
            if isinstance(operator, Operator):
                pass
                # operator.estimate(source_coordinates)
