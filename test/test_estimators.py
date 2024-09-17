"""
Test built-in Estimators.
"""

from typing import Callable, Dict

import numpy as np
import pytest

from transformo import TransformoParametersInvalidException
from transformo.estimators import DummyEstimator, HelmertTranslation, Operator


def test_estimator(source_coordinates, target_coordinates):
    """."""
    estimator = DummyEstimator(name="captaindumbdumb")

    assert isinstance(estimator, Operator)

    estimator.estimate(source_coordinates, target_coordinates, None, None)


def test_3param_helmert():
    """."""
    estimator = HelmertTranslation(name="anything_really")

    # Without specifying any parameters we should
    with pytest.raises(TransformoParametersInvalidException):
        # Just doing something with the T property here to trigger the exception
        np.sum(estimator.T)

    # Let's estimate some parameters...
    source_coordinates = np.zeros(shape=(3, 10))
    target_coordinates = np.ones(shape=(3, 10))
    estimator.estimate(source_coordinates, target_coordinates, None, None)

    # ... , because the HelmertTranslation is just a basic average of the
    # source and target coordinates we can easily predict result
    assert np.prod(estimator.T) == 1
