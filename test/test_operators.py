"""
Test built-in Operator.
"""

from typing import Literal

import numpy as np
import pytest

from transformo import TransformoNotImplemented
from transformo.operators import DummyOperator, HelmertTranslation, Operator
from transformo.typing import CoordinateMatrix


def test_base_operator(source_coordinates):
    """
    Test the functionality of the base Operator.

    It has abstract methods so we shouldn't be able to instantiate it
    but that can be circumvented by creating a child that implements the
    abstract methods. Additionally, the "soft" abstract methods `inverse()`
    and `estimate()` checked to see if they raise `TransformoNotImplemented`.
    """

    class ChildOperator(Operator):
        """ "
        For further testing of the base operator - implements `forward()`
        to avoid exceptions when instantiating the base `Operator` class.
        """

        type: Literal["child_operator"] = "child_operator"

        def forward(self, coordinates: CoordinateMatrix) -> CoordinateMatrix:
            return coordinates

        def _parameter_dict(self) -> dict[str, str | float]:
            return {}

    with pytest.raises(TypeError):
        Operator()

    operator = ChildOperator()
    assert isinstance(operator, Operator)
    assert isinstance(operator, ChildOperator)

    with pytest.raises(TransformoNotImplemented):
        operator.inverse(source_coordinates)

    with pytest.raises(TransformoNotImplemented):
        operator.estimate(source_coordinates, source_coordinates, None, None)

    # Let's check that children of Operator is registered properly in the
    # class method `get_subclasses()`.
    subclasses = Operator.get_subclasses()
    assert Operator in subclasses
    assert ChildOperator in subclasses

    # Some checks for the `parameters` property
    assert operator.parameters == operator._parameter_dict()
    assert operator.parameters == {}


def test_dummyoperator(source_coordinates, target_coordinates):
    """."""
    operator = DummyOperator(name="captaindumbdumb")

    assert isinstance(operator, Operator)

    assert np.all(source_coordinates == operator.forward(source_coordinates))
    assert np.all(source_coordinates == operator.inverse(source_coordinates))

    operator.estimate(source_coordinates, target_coordinates, None, None)


def test_helmerttranslation():
    """."""
    helmert_with_no_parameters = HelmertTranslation(name="anything_really")

    # Without specifying any parameters we should
    print(helmert_with_no_parameters.T)
    assert np.sum(helmert_with_no_parameters.T) == 0.0
    assert helmert_with_no_parameters._transformation_parameters_given is False

    helmert_with_one_parameter = HelmertTranslation(name="anything_really", y=5.0)
    print(helmert_with_one_parameter.T)
    assert np.sum(helmert_with_one_parameter.T) == 5
    assert helmert_with_one_parameter._transformation_parameters_given is True

    # Let's estimate some parameters...
    source_coordinates = np.zeros(shape=(10, 3))
    target_coordinates = np.ones(shape=(10, 3))
    helmert_with_no_parameters.estimate(
        source_coordinates, target_coordinates, None, None
    )

    # ... , because the HelmertTranslation is just a basic average of the
    # source and target coordinates we can easily predict result
    assert np.prod(helmert_with_no_parameters.T) == 1

    # A few final tests
    op = HelmertTranslation(x=3, y=5, z=10)

    # Can we roundtrip the `forward` and `inverse` methods
    roundtripped_coordinates = op.inverse(op.forward(source_coordinates))
    print(roundtripped_coordinates)
    assert np.all(source_coordinates == roundtripped_coordinates)

    # does the `Operator.paramers` property work as expected?
    assert len(op.parameters) == 3
    assert op.parameters["x"] == 3
    assert op.parameters["y"] == 5
    assert op.parameters["z"] == 10
