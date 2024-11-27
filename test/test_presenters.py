import json
from typing import Literal

import pytest

from transformo.datasources import CsvDataSource, DataSource
from transformo.operators import DummyOperator, HelmertTranslation, Operator
from transformo.presenters import (
    CoordinatePresenter,
    DummyPresenter,
    Presenter,
    PROJPresenter,
)


def test_base_presenter():
    """
    Test the functionality of the base Presenter.

    It has abstract methods so we shouldn't be able to instantiate it
    but that can be circumvented by creating a child that implements the
    abstract methods.
    """

    class ChildPresenter(Presenter):
        """ "
        For further testing of the base presenter.
        """

        type: Literal["child_presenter"] = "child_presenter"

        def evaluate(
            self, operators: list[Operator], results: list[DataSource]
        ) -> None:
            """Does nothing."""

        def as_json(self) -> str:
            """Returns the simplest JSON string possible."""

            return "{}"

        def as_markdown(self) -> str:
            """Returns the simplest string possible."""
            return ""

    with pytest.raises(TypeError):
        Presenter()

    operator = ChildPresenter()
    assert isinstance(operator, Presenter)
    assert isinstance(operator, ChildPresenter)

    # Let's check that children of Presenter is registered properly in the
    # class method `get_subclasses()`.
    subclasses = Presenter.get_subclasses()
    assert Presenter in subclasses
    assert ChildPresenter in subclasses


def test_presenter_name_property():
    """
    Test the Presenter.presenter_name property.
    """
    presenter_without_given_name = DummyPresenter()
    assert presenter_without_given_name.presenter_name == "dummy_presenter"

    presenter_with_name = DummyPresenter(name="The dumb presenter")
    assert presenter_with_name.presenter_name == "The dumb presenter"


def test_proj_presenter():
    """
    Test that the PROJPresenter can return a proper PROJstring.
    """

    # Operators
    dummy = DummyOperator()
    helmert = HelmertTranslation()
    helmert_with_params = HelmertTranslation(x=3.42, y=534.533, z=1234.5678)
    helmert_with_one_params = HelmertTranslation(y=432.52)

    presenter_with_no_operators = PROJPresenter()
    presenter_with_no_operators.evaluate(operators=[], results=[])

    assert presenter_with_no_operators.as_json() == '{"projstring": "+proj=noop"}'

    presenter_with_one_operator = PROJPresenter()
    presenter_with_one_operator.evaluate(operators=[helmert], results=[])
    assert presenter_with_one_operator.as_json() == '{"projstring": "+proj=noop"}'

    presenter_with_several_operators = PROJPresenter()
    presenter_with_several_operators.evaluate(
        operators=[dummy, helmert_with_one_params, helmert_with_params], results=[]
    )

    expected_pipeline = "+proj=pipeline +step +proj=helmert +y=432.52 +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678"
    assert (
        presenter_with_several_operators.as_json()
        == f'{{"projstring": "{expected_pipeline}"}}'
    )

    expected_pipeline = """
Transformation parameters given as a [PROJ](https://proj.org/) string.
```
+proj=pipeline
  +step +proj=helmert +y=432.52
  +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678
```
""".strip()

    print(presenter_with_several_operators.as_markdown())
    assert presenter_with_several_operators.as_markdown() == expected_pipeline


def test_coordinate_presenter(files):
    """
    .
    """
    p = CoordinatePresenter()

    ds1 = CsvDataSource(filename=files["dk_cors_itrf2014.csv"])
    ds2 = CsvDataSource(filename=files["dk_cors_etrs89.csv"])

    p.evaluate(operators=[], results=[ds1, ds2])
    results = json.loads(p.as_json())

    # A few sanity checks of the JSON data
    print(results)
    assert results[0]["BUDP"][0] == ds1.coordinates[0].x
    assert results[1]["BUDP"][0] == ds2.coordinates[0].x

    assert results[0]["FYHA"][2] == ds1.coordinates[3].z
    assert results[1]["FYHA"][2] == ds2.coordinates[3].z

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
