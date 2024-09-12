"""
Test the pipeline class.
"""

from pathlib import Path
from typing import Callable, Dict

from transformo.datasources import CsvDataSource
from transformo.estimators import DummyEstimator, DummyTransformation
from transformo.pipeline import TransformoPipeline


def test_pipeline(datasource_factory: Callable) -> None:
    """
    Test basic instantiation of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[datasource_factory(), datasource_factory()],
        target_data=[datasource_factory(), datasource_factory()],
        operators=[DummyTransformation(), DummyEstimator()],
    )

    assert isinstance(pipeline, TransformoPipeline)

    # Test that source/target_coordinates properties are working as intended
    n_coordinates = 2 * 10  # 2 datasources with 10 coordinates each
    assert pipeline.source_coordinates.shape == (n_coordinates, 3)
    assert pipeline.target_coordinates.shape == (n_coordinates, 3)

    assert (
        pipeline.source_coordinates[0, 0]
        == pipeline.source_data[0].coordinates[0].vector[0]
    )
    assert (
        pipeline.source_coordinates[15, 2]
        == pipeline.source_data[1].coordinates[5].vector[2]
    )
    assert (
        pipeline.target_coordinates[7, 0]
        == pipeline.target_data[0].coordinates[7].vector[0]
    )
    assert (
        pipeline.target_coordinates[19, 2]
        == pipeline.target_data[1].coordinates[9].vector[2]
    )


def test_pipeline_json_serilization(files: dict) -> None:
    """
    Test JSON serilization of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[CsvDataSource(filename=files["dk_cors_itrf2014.csv"])],
        target_data=[CsvDataSource(filename=files["dk_cors_etrs89.csv"])],
        operators=[DummyTransformation(), DummyEstimator()],
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
        operators=[DummyTransformation(), DummyEstimator()],
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
