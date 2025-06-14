"""
Test the pipeline class.
"""

import json
from typing import Callable

import pytest

from transformo.datasources import CsvDataSource, DataSource
from transformo.datatypes import Coordinate
from transformo.operators import DummyOperator, HelmertTranslation
from transformo.pipeline import Pipeline
from transformo.presenters import CoordinatePresenter, DummyPresenter, PROJPresenter


def test_pipeline(datasource_factory: Callable) -> None:
    """
    Test basic instantiation of a Pipeline.
    """
    pipeline = Pipeline(
        source_data=[datasource_factory(), datasource_factory()],
        target_data=[datasource_factory(), datasource_factory()],
        operators=[DummyOperator(), DummyOperator()],
        presenters=[DummyPresenter(), DummyPresenter()],
    )

    assert isinstance(pipeline, Pipeline)

    # Test that source/target_coordinates properties are working as intended
    n_coordinates = 2 * 10  # 2 datasources with 10 coordinates each
    assert pipeline.source_coordinates.shape == (n_coordinates, 4)
    assert pipeline.target_coordinates.shape == (n_coordinates, 4)


def test_pipeline_yaml_serilization(files: dict) -> None:
    """
    Test YAML serilization of a Pipeline.
    """
    pipeline = Pipeline(
        source_data=[
            CsvDataSource(name="itrf2024", filename=files["dk_cors_itrf2014.csv"])
        ],
        target_data=[
            CsvDataSource(name="etrs89", filename=files["dk_cors_etrs89.csv"])
        ],
        operators=[DummyOperator(), DummyOperator()],
        presenters=[DummyPresenter(), DummyPresenter()],
    )

    serialized_yaml = pipeline.to_yaml()
    print(serialized_yaml)

    new_pipeline = Pipeline.from_yaml(yaml=serialized_yaml)

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

    pipeline = Pipeline(
        source_data=[source],
        target_data=[target],
        operators=[helmert_transformation, helmert_estimation],
        presenters=[DummyPresenter(), DummyPresenter()],
    )

    pipeline.process()

    print(helmert_transformation.parameters)
    print(helmert_estimation.parameters)
    assert helmert_estimation.y == pytest.approx(50)


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

    pipeline = Pipeline(
        source_data=[source],
        target_data=[target],
        operators=[helmert_transformation, helmert_estimation],
        presenters=[PROJPresenter(), DummyPresenter()],
    )

    pipeline.process()

    results = pipeline.results
    source = pipeline.all_source_data
    target = pipeline.all_target_data

    # check expected residuals
    assert len(results) == 2  # we have added two operators to the pipeline

    # difference from source to step one - we expect a y-offset of 150 m,
    # as specified with the given parameter for `helmert_transformation`
    assert results[0].coordinates[0].x - source.coordinates[0].x == 0
    assert results[0].coordinates[0].y - source.coordinates[0].y == 150
    assert results[0].coordinates[0].z - source.coordinates[0].z == 0

    # difference between step two and one
    assert results[1].coordinates[0].x - results[0].coordinates[0].x == pytest.approx(
        10
    )
    assert results[1].coordinates[0].y - results[0].coordinates[0].y == pytest.approx(
        50
    )
    assert results[1].coordinates[0].z - results[0].coordinates[0].z == pytest.approx(
        3000
    )

    # difference between step two and target coordinates
    assert target.coordinates[0].x - results[1].coordinates[0].x == pytest.approx(0)
    assert target.coordinates[0].y - results[1].coordinates[0].y == pytest.approx(0)
    assert target.coordinates[0].z - results[1].coordinates[0].z == pytest.approx(0)


def test_pipeline_results_as_markdown(files: dict) -> None:
    """
    Test `results_as_markdown` method.

    Not the best test in the world, but will catch some regressions
    """
    pipeline = Pipeline(
        source_data=[CsvDataSource(filename=files["dk_cors_itrf2014.csv"])],
        target_data=[CsvDataSource(filename=files["dk_cors_etrs89.csv"])],
        operators=[HelmertTranslation()],
        presenters=[PROJPresenter(), CoordinatePresenter()],
    )

    pipeline.process()

    markdown = pipeline.results_as_markdown()
    print(markdown)

    assert markdown.splitlines()[0] == "# Transformo Results"
    assert markdown.splitlines()[1].startswith("*Created with Transformo version")
    assert markdown.splitlines()[3] == "## proj_presenter"
    assert markdown.splitlines()[16].startswith("|Station|      x       |")
    assert markdown.splitlines()[29].startswith("### Step 1: HelmertTranslation(x")


def test_pipeline_results_as_json(files: dict) -> None:
    """
    Test `results_as_json` method.

    Not the best test in the world, but will catch some regressions
    """
    pipeline = Pipeline(
        source_data=[CsvDataSource(filename=files["dk_cors_itrf2014.csv"])],
        target_data=[CsvDataSource(filename=files["dk_cors_etrs89.csv"])],
        operators=[HelmertTranslation()],
        presenters=[
            PROJPresenter(name="PROJ"),
            CoordinatePresenter(name="Coordinates"),
        ],
    )

    pipeline.process()

    jsondata = pipeline.results_as_json()
    data = json.loads(jsondata)

    assert "PROJ" in data.keys()
    assert "Coordinates" in data.keys()


def test_pipeline_processing_commands(caplog, datasource: DataSource) -> None:
    """
    Test the use of pre- and post-processing commands in a Pipeline.
    """
    pipeline = Pipeline(
        source_data=[datasource],
        target_data=[datasource],
        operators=[DummyOperator()],
        presenters=[DummyPresenter()],
        pre_processing_commands=["echo pre-process", "python --version"],
        post_processing_commands=["echo post-process 1", "echo post-process 2"],
    )

    pipeline.process()

    log_captures = [msg for (_, _, msg) in caplog.record_tuples]

    assert "pre-process" in log_captures
    assert "post-process 1" in log_captures
    assert "post-process 2" in log_captures
