"""
Tests for transformo.datasources.CsvDatasource
"""

from pathlib import Path

import pytest
from pydantic_core import ValidationError

from transformo.datasources import CsvColumns, CsvDataSource


def test_csvdatasource(files: dict[str, Path]) -> None:
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

    # We've got the same stations in both of the used test files,
    # so let's check that they've been read as expected
    test_stations = set(
        ["BUDP", "ESBC", "FER5", "FYHA", "GESR", "HABY", "HIRS", "SMID", "SULD", "TEJH"]
    )
    assert test_stations == set(c.station for c in with_header.coordinates)
    assert test_stations == set(c.station for c in without_header.coordinates)
    assert test_stations == set(c.station for c in from_filename_string.coordinates)


def test_csv_column_order(files: dict[str, Path]) -> None:
    """
    Test re-ordering of columns.
    """

    normal_column_order = CsvDataSource(filename=files["dk_cors_etrs89.csv"])

    custom_column_order = CsvDataSource(
        filename=files["dk_cors_etrs89.csv"],
        # note, weights are not read here
        columns=["station", "t", "y", "z", "x", "sz", "sx", "skip", "skip", "sy"],
    )

    assert custom_column_order.columns[0] == CsvColumns.STATION
    assert custom_column_order.columns[1] == CsvColumns.T
    assert custom_column_order.columns[2] == CsvColumns.Y
    assert custom_column_order.columns[3] == CsvColumns.Z
    assert custom_column_order.columns[4] == CsvColumns.X
    assert custom_column_order.columns[5] == CsvColumns.SZ
    assert custom_column_order.columns[6] == CsvColumns.SX
    assert custom_column_order.columns[7] == CsvColumns.SKIP
    assert custom_column_order.columns[8] == CsvColumns.SKIP
    assert custom_column_order.columns[9] == CsvColumns.SY

    assert custom_column_order.coordinates[0].y == normal_column_order.coordinates[0].x
    assert custom_column_order.coordinates[1].x == normal_column_order.coordinates[1].z
    assert (
        custom_column_order.coordinates[2].sz == normal_column_order.coordinates[2].sx
    )


def test_csv_invalid_column_names(files: dict[str, Path]) -> None:
    """Check error is raised when specifying invalid column types"""

    with pytest.raises(ValidationError):
        CsvDataSource(
            filename=files["dk_cors_etrs89.csv"],
            # note, weights are not read here
            columns=[
                "stations",
                "timestamp",
                "y",
                "z",
                "x",
                "sz",
                "sx",
                "skip",
                "skip",
                "sy",
            ],
        )


def test_csv_too_few_columns_specified(files: dict[str, Path]) -> None:

    with pytest.raises(ValidationError):
        CsvDataSource(
            filename=files["dk_cors_etrs89.csv"],
            # note, weights are not read here
            columns=["station", "x", "y"],
        )
