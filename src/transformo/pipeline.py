"""
Transformo pipeline classes.
"""

from __future__ import annotations

from typing import Annotated, Union

import pydantic
import pydantic_yaml

from transformo.datasources import DataSource
from transformo.protocols import DataSourceLike


class TransformoPipeline(pydantic.BaseModel):
    """The backbone of Transfomo"""

    source_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]
    target_data: list[Annotated[Union[DataSource.get_subclasses()], pydantic.Field(discriminator="type")]]  # type: ignore[valid-type]

    def __init__(
        self,
        source_data: list[DataSourceLike],
        target_data: list[DataSourceLike],
    ) -> None:
        """Set up for pipelines"""
        super().__init__(source_data=source_data, target_data=target_data)

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
