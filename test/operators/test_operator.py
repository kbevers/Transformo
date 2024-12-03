"""
Test built-in Operator.
"""

from typing import Literal

import numpy as np
import pytest

from transformo._typing import CoordinateMatrix
from transformo.datatypes import Parameter
from transformo.operators import DummyOperator, Operator


def test_base_operator(source_coordinates):
    """
    Test the functionality of the base Operator.

    It has abstract methods so we shouldn't be able to instantiate it
    but that can be circumvented by creating a child that implements the
    abstract methods. Additionally, the "soft" abstract methods `inverse()`
    and `estimate()` checked to see if they raise `NotImplementedError`.
    """

    class ChildOperator(Operator):
        """ "
        For further testing of the base operator - implements `forward()`
        to avoid exceptions when instantiating the base `Operator` class.
        """

        type: Literal["child_operator"] = "child_operator"

        def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
            return coordinates

        def _proj_name(self) -> str:
            return "noop"

        def _parameter_list(self) -> list[Parameter]:
            return []

    with pytest.raises(TypeError):
        Operator()

    operator = ChildOperator()
    assert isinstance(operator, Operator)
    assert isinstance(operator, ChildOperator)

    with pytest.raises(NotImplementedError):
        operator.inverse(source_coordinates)

    with pytest.raises(NotImplementedError):
        operator.estimate(source_coordinates, source_coordinates, None, None)

    # Let's check that children of Operator is registered properly in the
    # class method `get_subclasses()`.
    subclasses = Operator.get_subclasses()
    assert Operator in subclasses
    assert ChildOperator in subclasses

    # Some checks for the `proj_operation_name` property
    assert operator.proj_operation_name == operator._proj_name()
    assert operator.proj_operation_name == "noop"

    # Some checks for the `parameters` property
    assert operator.parameters == operator._parameter_list()
    assert operator.parameters == []

    # The `estimate()` method is not implemented so this should return False
    assert operator.can_estimate is False


def test_dummyoperator(source_coordinates, target_coordinates):
    """."""
    operator = DummyOperator(name="captaindumbdumb")

    assert isinstance(operator, Operator)

    assert np.all(source_coordinates == operator.forward(source_coordinates))
    assert np.all(source_coordinates == operator.inverse(source_coordinates))

    operator.estimate(source_coordinates, target_coordinates, None, None)

    # The `DummyOperator`` should be able to run the `estimate()` method
    assert operator.can_estimate is True
