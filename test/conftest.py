"""
Configuration of pytest
"""

import random
import string
from pathlib import Path
from typing import Callable, Dict

import numpy as np
import pytest

from transformo.datasources import CsvDataSource, DataSource
from transformo.datatypes import Coordinate
from transformo.operators import DummyOperator

# pylint: disable=redefined-outer-name


def random_string(n: int = 10):
    """
    Return a string of random, upper case letters.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


@pytest.fixture()
def files() -> Dict[str, Path]:
    """
    Return a dict of paths to known datafiles.

    The dict is indexed with keys consisting of the filenames of test files.

    Example:

        def test_something(files: dict) -> None:
            testfile = files["dk_cors.etrs89.csv"]
            assert isinstance(testfile, pathlib.Path)
    """

    # add new test files here, using a path relative to the "test" directory
    filenames = [
        # a csv-file *with* a header
        "data/dk_cors_etrs89.csv",
        # example of csv-file *without* a header
        "data/dk_cors_itrf2014.csv",
        # Bernese CRD files
        "data/dk_bernese52.CRD",
        "data/dk_bernese54.CRD",
    ]

    basepath = Path(__file__).parent.absolute()
    paths = [basepath / Path(f) for f in filenames]

    return {p.name: p for p in paths}


@pytest.fixture()
def coordinate_factory() -> Callable:
    """
    Coordinate factory fixture.

    Use this when several coordinates are needed in a test.
    """

    def factory():
        return Coordinate(
            station=random_string(4),
            t=2000 + random.random() * 25,
            x=500000 + random.random() * 1000000,
            y=500000 + random.random() * 1000000,
            z=500000 + random.random() * 1000000,
            sx=random.random(),
            sy=random.random(),
            sz=random.random(),
            w=random.random(),
        )

    return factory


@pytest.fixture()
def coordinate(coordinate_factory: Callable) -> Coordinate:
    """Coordinate fixture."""
    return coordinate_factory()


@pytest.fixture()
def source_coordinates(files: dict) -> np.typing.ArrayLike:
    """
    A numpy array with source coordinates.
    """
    ds = CsvDataSource(filename=files["dk_cors_itrf2014.csv"])
    return ds.coordinate_matrix


@pytest.fixture()
def target_coordinates(files: dict) -> np.typing.ArrayLike:
    """
    A numpy array with target coordinates.
    """
    ds = CsvDataSource(filename=files["dk_cors_etrs89.csv"])
    return ds.coordinate_matrix


@pytest.fixture()
def datasource_factory(coordinate_factory: Callable) -> Callable:
    """
    Datasource factory fixture.

    Use this when several DataSource's are needed in a test.
    """

    def factory():
        return DataSource(
            name=random_string(10),
            coordinates=[coordinate_factory() for _ in range(10)],
        )

    return factory


@pytest.fixture()
def datasource(datasource_factory: Callable) -> DataSource:
    """
    Datasource fixture.
    """
    return datasource_factory()


@pytest.fixture()
def dummy_operator() -> DummyOperator:
    """
    A dumb operator
    """
    return DummyOperator(name="Dummy")
