"""
Tests for transformo.datasources.CsvDatasource
"""

from pathlib import Path

from transformo.datasources import CsvDataSource


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
