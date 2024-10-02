import json
from typing import Literal

import pytest

from transformo.datasources import CsvDataSource, DataSource
from transformo.operators import DummyOperator, HelmertTranslation, Operator
from transformo.presenters import CoordinatePresenter, Presenter, PROJPresenter


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

        def as_text(self) -> str:
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

    expected_pipeline = """+proj=pipeline
  +step +proj=helmert +y=432.52
  +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678"""

    assert presenter_with_several_operators.as_text() == expected_pipeline


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
    expected_text = """===================================================
# Source coordinates
===================================================
BUDP    3513637.97424   778956.66526  5248216.59809
ESBC    3582104.73000   532590.21590  5232755.16250
FER5    3491111.17695   497995.12319  5296843.05030
FYHA    3611639.48454   635936.65951  5201015.01371
GESR    3625387.02679   765504.41925  5174102.86430
HABY    3507446.67528   704379.43463  5262740.43379
HIRS    3374902.76767   593115.83399  5361509.67641
SMID    3557910.95821   599176.95118  5242066.61051
SULD    3446393.93988   591713.40409  5316383.61894
TEJH    3522394.91330   933244.95952  5217231.61642

===================================================
# Target coordinates
===================================================
BUDP    3513638.56046   778956.18389  5248216.24817
ESBC    3582105.29700   532589.72930  5232754.80840
FER5    3491111.73600   497994.64800  5296842.69400
FYHA    3611640.06540   635936.17060  5201014.66830
GESR    3625387.61940   765503.92660  5174102.51330
HABY    3507447.25600   704378.95600  5262740.07900
HIRS    3374903.32690   593115.36900  5361509.30240
SMID    3557911.52730   599176.46810  5242066.25540
SULD    3446394.50549   591712.93860  5316383.26730
TEJH    3522395.52810   933244.47970  5217231.27310"""

    assert expected_text == p.as_text()
