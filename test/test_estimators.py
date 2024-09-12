"""
Test built-in Estimators.
"""

from typing import Callable, Dict

import numpy as np

from transformo.estimators import (
    DummyTransformation,
    Estimator,
    Helmert3ParameterEstimator,
    Operator,
    Transformation,
)


def test_transformations(source_coordinates, target_coordinates):
    """Test basic functionality of Transformation classes."""

    t = DummyTransformation()
    assert isinstance(t, Operator)
    assert isinstance(t, Transformation)

    assert np.all(t.forward(source_coordinates) == source_coordinates)


def test_estimator(source_coordinates, target_coordinates):
    """."""
    estimator = Helmert3ParameterEstimator()

    assert isinstance(estimator, Operator)
    assert isinstance(estimator, Estimator)

    estimator.estimate(source_coordinates, target_coordinates, None, None)
