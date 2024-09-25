from typing import Literal

import numpy as np
import pytest

from transformo import TransformoNotImplemented
from transformo.datasources import DataSource
from transformo.operators import DummyOperator, HelmertTranslation, Operator
from transformo.presenters import Presenter, PROJPresenter
from transformo.typing import CoordinateMatrix


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

        def parse_results(
            self, operators: list[Operator], results: list[DataSource]
        ) -> None:
            """Does nothing."""

        def as_json(self) -> str:
            """Returns the simplest JSON string possible."""

            return "{}"

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

    presenter_with_no_operators = PROJPresenter()
    presenter_with_no_operators.parse_results(operators=[], results=[])

    assert presenter_with_no_operators.as_json() == '{"projstring": "+proj=noop"}'

    presenter_with_one_operator = PROJPresenter()
    presenter_with_one_operator.parse_results(operators=[helmert], results=[])
    assert presenter_with_one_operator.as_json() == '{"projstring": "+proj=helmert"}'

    presenter_with_several_operators = PROJPresenter()
    presenter_with_several_operators.parse_results(
        operators=[dummy, helmert, helmert_with_params], results=[]
    )
    assert (
        presenter_with_several_operators.as_json()
        == '{"projstring": "+proj=pipeline +step +proj=noop +step +proj=helmert +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678"}'
    )

    txtprojstring = """
+proj=pipeline
  +step +proj=noop
  +step +proj=helmert
  +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678""".strip()  # removes beginning \n

    assert presenter_with_several_operators.as_text() == txtprojstring
