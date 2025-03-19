from datetime import datetime

import pydantic
import pytest

from transformo.datasources import BerneseCrdDataSource
from transformo.datasources.bernese import (
    crd_line_to_coordinate,
    datetime_to_decimal_year,
)

crd_line_test_data = [
    (
        "  2  BUDD 10101S001    3513649.04104   778955.02287  5248202.12784    A",
        ("BUDD", 3513649.04104, 778955.02287, 5248202.12784, "A"),
    ),
    (
        "  2  BUDD 10101S001    3513649.04138   778955.02303  5248202.12838    A      GRE",
        ("BUDD", 3513649.04138, 778955.02303, 5248202.12838, "A"),
    ),
    (
        "  5  ESBH 10115M002    3585278.72001   531971.41288  5230646.6845",
        ("ESBH", 3585278.72001, 531971.41288, 5230646.6845, None),
    ),
    (
        "920  KELY              1575559.29890 -1941827.91620  5848076.48160    A",
        ("KELY", 1575559.29890, -1941827.91620, 5848076.48160, "A"),
    ),
]


@pytest.mark.parametrize("crd_line,expected", crd_line_test_data)
def test_crd_line_to_coordinate(crd_line, expected):

    print(crd_line)
    print(expected)
    station, x, y, z, flag = expected

    c = crd_line_to_coordinate(crd_line)
    assert c.station == station
    assert c.x == x
    assert c.y == y
    assert c.z == z
    assert c.flag == flag


data = [
    (datetime(2024, 1, 1, 0, 0, 0), 2024.0),
    (datetime(2024, 12, 31, 23, 59, 59), 2024.999999),
    (datetime(1996, 8, 15, 0, 0, 0), 1996.623),
]


@pytest.mark.parametrize("date,expected", data)
def test_datetime_to_decimal_year(date, expected):
    print(date, expected)
    assert datetime_to_decimal_year(date) == pytest.approx(expected, 0.00001)


def test_crd_datasource(files):
    "Check if we can read files without any problems."

    ds1 = BerneseCrdDataSource(filename=files["dk_bernese52.CRD"])
    ds2 = BerneseCrdDataSource(filename=files["dk_bernese54.CRD"])

    assert len(ds1.stations) > 0
    assert len(ds2.stations) > 0

    assert ds1.coordinates[0].x == 3738358.14966
    assert ds2.coordinates[3].z == 5232755.16261


def test_crd_datasource_discard_flags(files):
    "Check that coordinates with certain flags are discarded."
    ds1 = BerneseCrdDataSource(filename=files["dk_bernese52.CRD"], discard_flags=["W"])
    ds2 = BerneseCrdDataSource(filename=files["dk_bernese54.CRD"], discard_flags=["A"])

    assert "ESBH" in ds1.stations
    assert "ESBH" in ds2.stations

    assert ds1.coordinates[0].t == pytest.approx(2022.8945)

    assert len(ds1.stations) == 25
    assert len(ds2.stations) == 9


def test_crd_datasource_uncertainties(files):
    """Check that setting uncertainties works as expected."""
    sx = 0.0523
    sy = 0.0452
    sz = 0.3230

    ds = BerneseCrdDataSource(
        filename=files["dk_bernese52.CRD"],
        discard_flags=["W"],
        sx=sx,
        sy=sy,
        sz=sz,
    )

    for c in ds.coordinates:
        assert c.sx == sx
        assert c.sy == sy
        assert c.sz == sz

    with pytest.raises(pydantic.ValidationError):
        ds = BerneseCrdDataSource(
            filename=files["dk_bernese52.CRD"],
            discard_flags=["W"],
            sx=-0.01,
            sy=-1.0,
            sz=-0.05,
        )


def test_crd_datasource_weight(files):
    """Check that setting the global station weight works as expected."""
    w = 0.92

    ds = BerneseCrdDataSource(
        filename=files["dk_bernese52.CRD"],
        discard_flags=["W"],
        w=w,
    )

    for c in ds.coordinates:
        assert c.w == w

    with pytest.raises(pydantic.ValidationError):
        ds = BerneseCrdDataSource(
            filename=files["dk_bernese52.CRD"],
            discard_flags=["W"],
            w=-1.0,
        )


def test_crd_datasource_epoch_override(files):
    """Check that setting the global station weight works as expected."""
    epoch = 2099.99

    ds = BerneseCrdDataSource(
        filename=files["dk_bernese54.CRD"],
        discard_flags=["W"],
        t=epoch,
    )

    for c in ds.coordinates:
        assert c.t == epoch
