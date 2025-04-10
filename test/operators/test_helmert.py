"""
Tests for transformo.operators.helmert
"""

import numpy as np

from transformo.datatypes import Parameter
from transformo.operators import HelmertTranslation


def test_helmerttranslation_can_estimate():
    """Check if the two principal modes of operation can be invoked."""
    helmert_with_no_parameters = HelmertTranslation(name="anything_really")

    assert helmert_with_no_parameters.can_estimate is True

    # Without specifying any parameters we should
    print(helmert_with_no_parameters.T)
    assert np.sum(helmert_with_no_parameters.T) == 0.0
    assert helmert_with_no_parameters._transformation_parameters_given is False

    helmert_with_one_parameter = HelmertTranslation(name="anything_really", y=5.0)
    assert helmert_with_one_parameter.can_estimate is False

    print(helmert_with_one_parameter.T)
    assert np.sum(helmert_with_one_parameter.T) == 5
    assert helmert_with_one_parameter._transformation_parameters_given is True


def test_helmerttranslation_as_estimator():
    """
    Test parameter estimation
    """

    helmert_with_no_parameters = HelmertTranslation(name="anything_really")

    # Let's estimate some parameters...
    source_coordinates = np.zeros(shape=(10, 3))
    target_coordinates = np.ones(shape=(10, 3))
    weigths = np.ones(shape=(10, 3))
    helmert_with_no_parameters.estimate(
        source_coordinates, target_coordinates, weigths, weigths
    )

    # ... , because the HelmertTranslation is just a basic average of the
    # source and target coordinates we can easily predict result
    assert np.prod(helmert_with_no_parameters.T) == 1


def test_helmerttranslation_estimation_with_weights():
    """
    Test that parameters are estimated correctly when using weights.
    """

    source_coordinates = np.array(
        [
            [100, 100, 100],
            [50, 50, 50],
            [50, 50, 50],
        ]
    )
    target_coordinates = np.zeros(shape=(3, 3))

    source_weights = np.array(
        [
            [2, 0.5, 0.0],
            [1, 1, 1],
            [1, 1, 1],
        ]
    )
    target_weights = np.array(
        [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1],
        ]
    )

    helmert = HelmertTranslation()
    helmert.estimate(
        source_coordinates, target_coordinates, source_weights, target_weights
    )

    print(helmert.T)

    # a negative value is expected because we look at coordinate difference,
    # and since the target coordinates are zero we need to subtract from the source
    # to get where we are going.
    assert helmert.T[0] == -(100 * 2 + 50 + 50) / (2 + 1 + 1)
    assert helmert.T[1] == -(100 * 0.5 + 50 + 50) / (0.5 + 1 + 1)
    assert helmert.T[2] == -(50 + 50) / 2


def test_helmerttranslation_as_operator():
    """
    Test that HelmertTranslation works as an operator when given parameters.
    """

    # A few final tests
    op = HelmertTranslation(x=3, y=5, z=10)

    # Can we roundtrip the `forward` and `inverse` methods
    source_coordinates = np.zeros(shape=(10, 3))
    roundtripped_coordinates = op.inverse(op.forward(source_coordinates))
    print(roundtripped_coordinates)
    assert np.all(source_coordinates == roundtripped_coordinates)

    # does the `Operator.parameters` property work as expected?
    assert len(op.parameters) == 3
    assert op.parameters[0] == Parameter("x", 3)
    assert op.parameters[1] == Parameter("y", 5)
    assert op.parameters[2] == Parameter("z", 10)
