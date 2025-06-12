"""
Test built-in datasources.
"""

from typing import Callable

import numpy as np
import pytest

from transformo._typing import CoordinateMatrix
from transformo.core import CoordinateOverrides
from transformo.datasources import CombinedDataSource, CsvDataSource, DataSource


def test_datasource(coordinate_factory: Callable) -> None:
    """Test that DataSource works as expected"""
    n = 10

    # Can we instantiate a DataSource from a coordinate list?
    ds1 = DataSource(name="test", coordinates=[coordinate_factory() for _ in range(n)])
    assert ds1.name == "test"
    assert len(ds1.coordinates) == n

    # Is the coordinate matrix property functioning as expected?
    assert isinstance(ds1.coordinate_matrix, np.ndarray)
    assert ds1.coordinate_matrix.shape == (n, 4)
    assert (ds1.coordinate_matrix[0, :] == ds1.coordinates[0].vector).all()

    # Can we add two datasources?
    ds2 = DataSource(coordinates=[coordinate_factory() for _ in range(n)])

    ds_combined = ds1 + ds2
    assert len(ds_combined.coordinates) == 2 * n
    assert ds_combined.coordinate_matrix.shape == (2 * n, 4)
    assert isinstance(ds_combined, DataSource)

    ds_combined2 = ds1
    for ds in [ds1, ds2]:
        ds_combined2 = ds_combined2 + ds

    assert len(ds_combined2.coordinates) == 3 * n
    assert ds_combined2.coordinate_matrix.shape == (3 * n, 4)
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


def test_datasource_sum(datasource_factory: DataSource) -> None:
    """
    Test DataSource.__sum__

    In particular the edge cases where at least one empty DataSource is part
    of the summation.
    """

    ds1 = datasource_factory()
    ds2 = datasource_factory()

    none_sum = DataSource(None) + DataSource(None)
    assert not none_sum.coordinates

    assert ds1 + DataSource(None) is ds1
    assert DataSource(None) + ds1 is ds1

    sum_ds = ds1 + ds2

    assert isinstance(sum_ds, CombinedDataSource)
    assert len(sum_ds.coordinates) == len(ds1.coordinates) + len(ds2.coordinates)


def test_combineddatasource(datasource_factory: DataSource) -> None:
    """
    Test mechanincs of CombinedDataSource.
    """
    first = datasource_factory()
    second = datasource_factory()
    # number of coordinates assigned by the factory
    n_coords = len(first.coordinates)

    combined = CombinedDataSource(first, second)

    assert isinstance(combined, CombinedDataSource)
    assert len(combined.coordinates) == 2 * n_coords

    combined2 = CombinedDataSource(combined, datasource_factory())
    assert isinstance(combined2, CombinedDataSource)
    assert len(combined2.coordinates) == 3 * n_coords


def test_datasource_origins(datasource_factory: DataSource) -> None:
    """
    Test properties DataSource.origins and CombinedDataSource.origins.

    The CombinedDataSource.origins property is recursive, here we test
    that it delivers the expected results, even when going a few levels
    deep.
    """
    first = datasource_factory()
    second = datasource_factory()
    third = datasource_factory()
    fourth = datasource_factory()

    combined = CombinedDataSource(first, second)

    # verify that DataSource.origins returns itself, wrapped in a list
    assert first == first.origins[0]
    assert second == second.origins[0]

    # verify that both datasource are returned in the combined origins list
    assert first in combined.origins
    assert second in combined.origins

    # verify recursion of origin property
    combined2 = CombinedDataSource(third, fourth)
    combined3 = CombinedDataSource(combined, combined2)

    assert len(combined3.origins) == 4
    assert first in combined3.origins
    assert second in combined3.origins
    assert third in combined3.origins
    assert fourth in combined3.origins

    level4 = combined3 + combined2
    assert len(level4.origins) == 4


def test_datasource_hash(files) -> None:
    """
    Test DataSource.__hash__()
    """
    csv1 = CsvDataSource(filename=files["dk_cors_etrs89.csv"])
    csv2 = CsvDataSource(filename=files["dk_cors_etrs89.csv"])

    assert hash(csv1) != hash(csv2)


def test_post_init_datasource_wide_overrides(coordinate_factory) -> None:
    """
    Test overrides that work on the entire datasource.
    """
    n = 2
    sx = 0.05
    sy = 0.12
    sz = 0.52
    w = 0.7
    t = 2099.99

    coordinates = [coordinate_factory() for _ in range(n)]
    ds = DataSource(
        name="test",
        coordinates=coordinates,
        sx=sx,
        sy=sy,
        sz=sz,
        w=w,
        t=t,
    )

    for c in ds.coordinates:
        assert c.sx == sx
        assert c.sy == sy
        assert c.sz == sz
        assert c.w == c.w
        assert c.t == c.t


def test_post_init_datasource_wide_overrides_childs(files) -> None:
    """
    Test that overrides work for childs of DataSource.
    """
    sx = 0.05
    sy = 0.12
    sz = 0.52
    w = 0.7
    t = 2099.99

    ds = CsvDataSource(
        filename=files["dk_cors_etrs89.csv"],
        sx=sx,
        sy=sy,
        sz=sz,
        w=w,
        t=t,
    )

    for c in ds.coordinates:
        assert c.sx == sx
        assert c.sy == sy
        assert c.sz == sz
        assert c.w == c.w
        assert c.t == c.t


def test_station_overrides(files) -> None:
    """Test that overriding values for certain station works."""
    ds = CsvDataSource(
        filename=files["dk_cors_etrs89.csv"],
        overrides={
            "BUDP": CoordinateOverrides(sx=0.01, w=2.0),
            "FYHA": CoordinateOverrides(sy=0.5, t=2099.0),
            "HIRS": CoordinateOverrides(x=0.0, y=0.0, z=0.0),
            "SULD": CoordinateOverrides(station="MULD", sz=0.42),
        },
    )

    for c in ds.coordinates:
        if c.station == "BUDP":
            assert c.sx == 0.01 and c.w == 2.0

        if c.station == "FYHA":
            assert c.sy == 0.5 and c.t == 2099.0

        if c.station == "HIRS":
            assert c.x == 0.0 and c.y == 0.0 and c.z == 0.0

        if c.station == "SULD":
            assert c.sz == 0.42
            assert c.station == "MULD"


def test_station_union(files) -> None:
    """
    Test DataSource.station_union().

    In the file `dk_cors_etrs89.csv` we have the following stations:

        BUDP, ESBC, FER5, FYHA, GESR, HABY, HIRS, SMID, SULD, TEJH

    By renaming some of them in the import we can simulate to different
    DataSources that includes different stations.
    """

    ds1 = CsvDataSource(filename=files["dk_cors_etrs89.csv"])
    ds2 = CsvDataSource(
        filename=files["dk_cors_etrs89.csv"],
        overrides={
            "BUDP": CoordinateOverrides(station="BIDP"),
            "FYHA": CoordinateOverrides(station="PYHA"),
            "HIRS": CoordinateOverrides(station="HALS"),
            "SULD": CoordinateOverrides(station="MULD"),
        },
    )

    union = ds1.station_union(ds2)
    expected_union = ["ESBC", "FER5", "GESR", "HABY", "SMID", "TEJH"]

    assert set(union) == set(expected_union)


def test_limit_to_stations(files) -> None:
    """Test DataSource.limit_to_stations()."""
    ds = CsvDataSource(
        filename=files["dk_cors_etrs89.csv"],
    )

    stations = ["BUDP", "ESBC"]
    ds.limit_to_stations(stations)
    limited_stations = [c.station for c in ds.coordinates]

    assert stations == limited_stations
