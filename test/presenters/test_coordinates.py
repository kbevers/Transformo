"""
Tests for transformo.presenters.coordinates
"""

import json

from transformo.datasources import CsvDataSource, DataSource
from transformo.datatypes import Coordinate
from transformo.presenters import (
    CoordinatePresenter,
    CoordinateType,
    ResidualPresenter,
    TopocentricResidualPresenter,
)


def test_coordinate_presenter(files, dummy_operator):
    """
    .
    """
    p = CoordinatePresenter()

    ds1 = CsvDataSource(filename=files["dk_cors_itrf2014.csv"])
    ds2 = CsvDataSource(filename=files["dk_cors_etrs89.csv"])

    p.evaluate(
        operators=[dummy_operator],
        source_data=ds1,
        target_data=ds2,
        results=[ds1],  # emmulate the dummy operator
    )
    results = json.loads(p.as_json())

    # A few sanity checks of the JSON data
    assert results[1]["BUDP"][0] == ds1.coordinates[0].x
    assert results[2]["BUDP"][0] == ds2.coordinates[0].x

    assert results[1]["FYHA"][2] == ds1.coordinates[3].z
    assert results[2]["FYHA"][2] == ds2.coordinates[3].z

    # Really just here to detect regressions
    expected_text = """
Source and target coordinates as well as intermediate results shown in tabular form.

### Source coordinates

|Station|      x       |      y      |      z       |     t     |
|-------|--------------|-------------|--------------|-----------|
| BUDP  | 3513637.9742 | 778956.6653 | 5248216.5981 | 2022.9301 |
| ESBC  | 3582104.7300 | 532590.2159 | 5232755.1625 | 2022.9301 |
| FER5  | 3491111.1770 | 497995.1232 | 5296843.0503 | 2022.9301 |
| FYHA  | 3611639.4845 | 635936.6595 | 5201015.0137 | 2022.9301 |
| GESR  | 3625387.0268 | 765504.4193 | 5174102.8643 | 2022.9301 |
| HABY  | 3507446.6753 | 704379.4346 | 5262740.4338 | 2022.9301 |
| HIRS  | 3374902.7677 | 593115.8340 | 5361509.6764 | 2022.9301 |
| SMID  | 3557910.9582 | 599176.9512 | 5242066.6105 | 2022.9301 |
| SULD  | 3446393.9399 | 591713.4041 | 5316383.6189 | 2022.9301 |
| TEJH  | 3522394.9133 | 933244.9595 | 5217231.6164 | 2022.9301 |

### Step 1: DummyOperator()

|Station|      x       |      y      |      z       |     t     |
|-------|--------------|-------------|--------------|-----------|
| BUDP  | 3513637.9742 | 778956.6653 | 5248216.5981 | 2022.9301 |
| ESBC  | 3582104.7300 | 532590.2159 | 5232755.1625 | 2022.9301 |
| FER5  | 3491111.1770 | 497995.1232 | 5296843.0503 | 2022.9301 |
| FYHA  | 3611639.4845 | 635936.6595 | 5201015.0137 | 2022.9301 |
| GESR  | 3625387.0268 | 765504.4193 | 5174102.8643 | 2022.9301 |
| HABY  | 3507446.6753 | 704379.4346 | 5262740.4338 | 2022.9301 |
| HIRS  | 3374902.7677 | 593115.8340 | 5361509.6764 | 2022.9301 |
| SMID  | 3557910.9582 | 599176.9512 | 5242066.6105 | 2022.9301 |
| SULD  | 3446393.9399 | 591713.4041 | 5316383.6189 | 2022.9301 |
| TEJH  | 3522394.9133 | 933244.9595 | 5217231.6164 | 2022.9301 |

### Target coordinates

|Station|      x       |      y      |      z       |     t     |
|-------|--------------|-------------|--------------|-----------|
| BUDP  | 3513638.5605 | 778956.1839 | 5248216.2482 | 2018.2400 |
| ESBC  | 3582105.2970 | 532589.7293 | 5232754.8084 | 2018.2400 |
| FER5  | 3491111.7360 | 497994.6480 | 5296842.6940 | 2018.2400 |
| FYHA  | 3611640.0654 | 635936.1706 | 5201014.6683 | 2018.2400 |
| GESR  | 3625387.6194 | 765503.9266 | 5174102.5133 | 2018.2400 |
| HABY  | 3507447.2560 | 704378.9560 | 5262740.0790 | 2018.2400 |
| HIRS  | 3374903.3269 | 593115.3690 | 5361509.3024 | 2018.2400 |
| SMID  | 3557911.5273 | 599176.4681 | 5242066.2554 | 2018.2400 |
| SULD  | 3446394.5055 | 591712.9386 | 5316383.2673 | 2018.2400 |
| TEJH  | 3522395.5281 | 933244.4797 | 5217231.2731 | 2018.2400 |
""".strip()

    print(p.as_markdown())
    assert expected_text == p.as_markdown()


def test_residual_presenter(dummy_operator):
    """
    Test the residual presenter.
    """

    model = DataSource(
        coordinates=[
            Coordinate("A", 2000, 0, 0, 0, 0, 0, 0),
            Coordinate("B", 2000, 0, 0, 0, 0, 0, 0),
        ]
    )

    target = DataSource(
        coordinates=[
            Coordinate("A", 2000, 2.5, 2.5, 2.5, 0, 0, 0, 0),
            Coordinate("B", 2000, 1, 0, 0, 0, 0, 0, 0),
        ]
    )

    presenter = ResidualPresenter()
    presenter.evaluate(
        operators=[dummy_operator],
        source_data=model,
        target_data=target,
        results=[model],
    )

    data = json.loads(presenter.as_json())

    assert data["residuals"]["A"][0] == 2.5
    assert data["residuals"]["B"][3] == 1.0

    print(data)
    print(presenter.as_markdown())


def test_topocentricresidual_presenter_degree(dummy_operator):
    """
    Test the topocentric residual presenter using coordinate type degrees.
    """

    model = DataSource(
        coordinates=[
            Coordinate("A", 2000, 12.6961326, 55.9078613, 23.523, 0, 0, 0),
            Coordinate("B", 2000, 12.5757822, 55.6813657, 7.067, 0, 0, 0),
        ]
    )
    target = DataSource(
        coordinates=[
            Coordinate("A", 2000, 12.6961374, 55.9078623, 23.585, 0, 0, 0),
            Coordinate("B", 2000, 12.5757852, 55.6813612, 7.012, 0, 0, 0),
        ]
    )

    presenter = TopocentricResidualPresenter(coordinate_type=CoordinateType.DEGREES)
    presenter.evaluate(
        operators=[],
        source_data=model,
        target_data=target,
        results=[model],
    )
