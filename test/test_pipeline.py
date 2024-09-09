"""
Test the pipeline class.
"""

from pathlib import Path
from typing import Callable, Dict

from transformo.datasources import CsvDataSource
from transformo.pipeline import TransformoPipeline


def test_pipeline(datasource_factory: Callable) -> None:
    """
    Test basic instantiation of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[datasource_factory(), datasource_factory()],
        target_data=[datasource_factory(), datasource_factory()],
    )

    assert isinstance(pipeline, TransformoPipeline)


def test_pipeline_json_serilization(files: dict) -> None:
    """
    Test JSON serilization of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[CsvDataSource(filename=files["dk_cors_itrf2014.csv"])],
        target_data=[CsvDataSource(filename=files["dk_cors_etrs89.csv"])],
    )

    serialized_json = pipeline.to_json()
    print(serialized_json)

    new_pipeline = TransformoPipeline.from_json(json=serialized_json)

    # Check that the same coordinates are present in the two pipelines
    assert (
        new_pipeline.source_data[0].coordinates == pipeline.source_data[0].coordinates
    )
    assert (
        new_pipeline.target_data[0].coordinates == pipeline.target_data[0].coordinates
    )

    # Check that the filenames are the same before and after serilization.
    # The types differ since the new pipeline contains a string versus the original
    # that has a Path, but they should refer to the same file
    assert new_pipeline.source_data[0].filename == str(pipeline.source_data[0].filename)
    assert new_pipeline.target_data[0].filename == str(pipeline.target_data[0].filename)


def test_pipeline_yaml_serilization(files: dict) -> None:
    """
    Test YAML serilization of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[
            CsvDataSource(name="itrf2024", filename=files["dk_cors_itrf2014.csv"])
        ],
        target_data=[
            CsvDataSource(name="etrs89", filename=files["dk_cors_etrs89.csv"])
        ],
    )

    serialized_yaml = pipeline.to_yaml()
    print(serialized_yaml)

    new_pipeline = TransformoPipeline.from_yaml(yaml=serialized_yaml)

    # Check that the same coordinates are present in the two pipelines
    assert (
        new_pipeline.source_data[0].coordinates == pipeline.source_data[0].coordinates
    )
    assert (
        new_pipeline.target_data[0].coordinates == pipeline.target_data[0].coordinates
    )

    # Check that the filenames are the same before and after serilization.
    # The types differ since the new pipeline contains a string versus the original
    # that has a Path, but they should refer to the same file
    assert new_pipeline.source_data[0].filename == str(pipeline.source_data[0].filename)
    assert new_pipeline.target_data[0].filename == str(pipeline.target_data[0].filename)

    assert new_pipeline.source_data[0].name == "itrf2024"
    assert new_pipeline.target_data[0].name == "etrs89"
