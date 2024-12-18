"""
Test built-in datasources.
"""

from typing import Callable

import numpy as np
import pytest

from transformo._typing import CoordinateMatrix
from transformo.datasources import DataSource


def test_datasource(coordinate_factory: Callable) -> None:
    """Test that DataSource works as expected"""
    n = 10

    # Can we instantiate a DataSource from a coordinate list?
    ds1 = DataSource(name="test", coordinates=[coordinate_factory() for _ in range(n)])
    assert ds1.name == "test"
    assert len(ds1.coordinates) == n

    # Is the coordinate matrix property functioning as expected?
    assert isinstance(ds1.coordinate_matrix, np.ndarray)
    assert ds1.coordinate_matrix.shape == (n, 3)
    assert (ds1.coordinate_matrix[0, :] == ds1.coordinates[0].vector).all()

    # Can we add two datasources?
    ds2 = DataSource(coordinates=[coordinate_factory() for _ in range(n)])

    ds_combined = ds1 + ds2
    assert len(ds_combined.coordinates) == 2 * n
    assert ds_combined.coordinate_matrix.shape == (2 * n, 3)
    assert isinstance(ds_combined, DataSource)

    ds_combined2 = ds1
    for ds in [ds1, ds2]:
        ds_combined2 = ds_combined2 + ds

    assert len(ds_combined2.coordinates) == 3 * n
    assert ds_combined2.coordinate_matrix.shape == (3 * n, 3)
    assert isinstance(ds_combined2, DataSource)


def test_datasource_update_coordinates(datasource: DataSource) -> None:
    """
    Test that the `update_coordinates` method works as expected.
    """

    n = len(datasource.coordinates)
    coordinates: CoordinateMatrix = np.ones((n, 3))

    new_datasource = datasource.update_coordinates(coordinates)

    for old, new in zip(datasource.coordinates, new_datasource.coordinates):
        assert old.station == new.station
        assert old.t == new.t
        assert np.all(old.stddev == new.stddev)
        assert np.all(old.weights == new.weights)
        assert new.x == 1
        assert new.y == 1
        assert new.z == 1

    too_many_coordiantes = np.ones((n + 1, 3))
    with pytest.raises(ValueError):
        datasource.update_coordinates(too_many_coordiantes)
