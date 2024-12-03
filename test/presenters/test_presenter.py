"""
Tests for Presenter and DummyPresenter
"""

from typing import Literal

import pytest

from transformo.datasources import DataSource
from transformo.operators import Operator
from transformo.presenters import DummyPresenter, Presenter


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
