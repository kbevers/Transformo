"""
Test built-in datasources.
"""

from pathlib import Path
from typing import Callable, Dict

import numpy as np

from transformo.datasources import CsvDataSource, DataSource


def test_datasource(coordinate_factory: Callable) -> None:
    """Test that DataSource works as expected"""
    n = 10

    # Can we instantiate a DataSource from a coordinate list?
    ds1 = DataSource(coordinates=[coordinate_factory() for _ in range(n)])
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


def test_csvdatasource(files: Dict[str, Path]) -> None:
    """
    Test the CsvReader
    """
    # this csv-file has a header
    with_header = CsvDataSource(filename=files["dk_cors_etrs89.csv"])
    assert isinstance(with_header, CsvDataSource)

    # no header in this csv file
    without_header = CsvDataSource(filename=files["dk_cors_itrf2014.csv"])
    assert isinstance(without_header, CsvDataSource)

    from_filename_string = CsvDataSource(filename=str(files["dk_cors_itrf2014.csv"]))
    assert isinstance(from_filename_string, CsvDataSource)

    # We've got the same stations in both of the used test files, so let's check that they've
    # been read as expected
    test_stations = set(
        ["BUDP", "ESBC", "FER5", "FYHA", "GESR", "HABY", "HIRS", "SMID", "SULD", "TEJH"]
    )
    assert test_stations == set(c.station for c in with_header.coordinates)
    assert test_stations == set(c.station for c in without_header.coordinates)
    assert test_stations == set(c.station for c in from_filename_string.coordinates)
