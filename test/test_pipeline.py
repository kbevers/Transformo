"""
Test the pipeline class.
"""

from pathlib import Path
from typing import Callable, Dict

from transformo import Coordinate
from transformo.datasources import CsvDataSource, DataSource
from transformo.operators import DummyOperator, HelmertTranslation
from transformo.pipeline import TransformoPipeline


def test_pipeline(datasource_factory: Callable) -> None:
    """
    Test basic instantiation of a TransformoPipeline.
    """
    pipeline = TransformoPipeline(
        source_data=[datasource_factory(), datasource_factory()],
        target_data=[datasource_factory(), datasource_factory()],
        operators=[DummyOperator(), DummyOperator()],
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
        operators=[DummyOperator(), DummyOperator()],
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
        operators=[DummyOperator(), DummyOperator()],
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


def test_pipeline_estimation_using_helmert_translation() -> None:
    """
    .
    """

    src_coords = [Coordinate("TEST", 2024.75, 0, 0, 0, 0, 0, 0, 1) for _ in range(10)]
    tgt_coords = [
        Coordinate("TEST", 2024.75, 10, 200, 3000, 0, 0, 0, 1) for _ in range(10)
    ]

    source = DataSource(coordinates=src_coords)
    target = DataSource(coordinates=tgt_coords)

    helmert_transformation = HelmertTranslation(y=150)
    helmert_estimation = HelmertTranslation()

    pipeline = TransformoPipeline(
        source_data=[source],
        target_data=[target],
        operators=[helmert_transformation, helmert_estimation],
    )

    pipeline.process()

    print(helmert_transformation.parameters)
    print(helmert_estimation.parameters)
    assert helmert_estimation.y == 50


def test_pipeline_access() -> None:
    """
    Test the intermediate results of a pipeline process.

    A pipeline of two steps is defined, the first is a transformation and the
    second is an estimation operation. Both are based on the HelmertTranslation
    as it's simple nature makes it easy to calculate the expected results
    beforehand. Here only one set of source/target coordinates is given which
    in turn simplifies the Helmert Operations to addition and subtraction between
    the steps.
    """
    src_coords = [Coordinate("TEST", 2024.75, 0, 0, 0, 0, 0, 0, 1) for _ in range(10)]
    tgt_coords = [
        Coordinate("TEST", 2024.75, 10, 200, 3000, 0, 0, 0, 1) for _ in range(10)
    ]

    source = DataSource(coordinates=src_coords)
    target = DataSource(coordinates=tgt_coords)

    helmert_transformation = HelmertTranslation(y=150)
    helmert_estimation = HelmertTranslation()

    pipeline = TransformoPipeline(
        source_data=[source],
        target_data=[target],
        operators=[helmert_transformation, helmert_estimation],
    )

    pipeline.process()

    # check expected residuals
    results = pipeline.results
    # difference from source to step one - we expect a y-offset of 150 m,
    # as specified with the given parameter for `helmert_transformation`
    assert results[1].coordinates[0].x - results[0].coordinates[0].x == 0
    assert results[1].coordinates[0].y - results[0].coordinates[0].y == 150
    assert results[1].coordinates[0].z - results[0].coordinates[0].z == 0
    # difference between step two and one
    assert results[2].coordinates[0].x - results[1].coordinates[0].x == 10
    assert results[2].coordinates[0].y - results[1].coordinates[0].y == 50
    assert results[2].coordinates[0].z - results[1].coordinates[0].z == 3000
    # difference between step two and target coordinates
    assert results[3].coordinates[0].x - results[2].coordinates[0].x == 0
    assert results[3].coordinates[0].y - results[2].coordinates[0].y == 0
    assert results[3].coordinates[0].z - results[2].coordinates[0].z == 0
