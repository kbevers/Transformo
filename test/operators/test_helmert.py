"""
Tests for transformo.operators.helmert
"""

import numpy as np

from transformo.datatypes import Parameter
from transformo.operators import HelmertTranslation


def test_helmerttranslation():
    """."""
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
    assert op.parameters[0] == Parameter("x", 3)
    assert op.parameters[1] == Parameter("y", 5)
    assert op.parameters[2] == Parameter("z", 10)
