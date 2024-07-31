"""
Transformo pipeline classes.
"""

from __future__ import annotations

import inspect
import sys
from collections import deque
from os import PathLike

import pydantic

from transformo.datasources import DataSource
from transformo.estimators import TransformoEstimator
from transformo.writers import TransformoWriter


class DatasourceConfig(pydantic.BaseModel):
    """Schema for configuration of a datasource."""

    name: str

    @classmethod
    @pydantic.field_validator("name")
    def check_valid_name(cls, name: str) -> str:
        """Validate name against known datasource classes"""
        for obj_name, obj in inspect.getmembers(sys.modules["transformo.datasources"]):
            if inspect.isclass(obj) and obj.__base__ is DataSource:
                if name == obj_name:
                    return name

        raise ValueError(f"Unknown DataSource: {name}")


class PipelineSchema(pydantic.BaseModel):
    """
    Schema for pipeline setup.

    Pydantic is used for it's data validation abilities.
    """


class TransformoPipeline:
    """The backbone of Transfomo"""

    source_data: list[DataSource]
    target_data: list[DataSource]

    def __init__(
        self,
        source_data: list[DataSource],
        target_data: list[DataSource],
        # estimators: deque[TransformoEstimator],
        # writers: list[TransformoWriter],
    ) -> None:
        """Set up for pipelines"""
        super().__init__()

        self.source_data = source_data
        self.target_data = target_data
        # self.estimators = estimators
        # self.writers = writers
