"""
Tests for transformo.operators.helmert
"""

import numpy as np
import pytest

from transformo.datatypes import Parameter
from transformo.operators import Helmert7Param, HelmertTranslation, RotationConvention
from transformo.transformer import Transformer


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


def test_helmert7param_instantiation():
    """
    Basic tests of instantiating the Helmert7Param class
    """
    h7 = Helmert7Param(
        convention=RotationConvention.COORDINATE_FRAME,
        x=1.0,
        y=1.0,
        z=1.0,
        rx=0.001,
        ry=0.002,
        rz=0.003,
        s=0.005,
    )

    assert isinstance(h7, Helmert7Param)
    assert h7.x == 1.0
    assert h7.y == 1.0
    assert h7.z == 1.0
    assert h7.rx == 0.001
    assert h7.ry == 0.002
    assert h7.rz == 0.003
    assert h7.s == 0.005

    assert h7._transformation_parameters_given is True
    assert h7.can_estimate is False

    h7 = Helmert7Param(convention=RotationConvention.COORDINATE_FRAME)

    assert h7._transformation_parameters_given is False
    assert h7.can_estimate is True


def test_helmert7param_parameters():
    """Test that Helmert7Param.parameters returns the correct values."""

    h7 = Helmert7Param(
        convention=RotationConvention.COORDINATE_FRAME,
        test_helmert7param_small_angle_approximation=True,
        x=1.0,
        y=1.0,
        z=1.0,
        rx=0.001,
        ry=0.002,
        rz=0.003,
        s=0.005,
    )

    for param in h7.parameters:
        print(param.name, param.value)

    assert h7.parameters[0].name == "x" and h7.parameters[0].value == 1.0
    assert h7.parameters[1].name == "y" and h7.parameters[1].value == 1.0
    assert h7.parameters[2].name == "z" and h7.parameters[2].value == 1.0
    assert h7.parameters[3].name == "rx" and h7.parameters[3].value == 0.001
    assert h7.parameters[4].name == "ry" and h7.parameters[4].value == 0.002
    assert h7.parameters[5].name == "rz" and h7.parameters[5].value == 0.003
    assert h7.parameters[6].name == "s" and h7.parameters[6].value == 0.005
    assert (
        h7.parameters[7].name == "convention"
        and h7.parameters[7].value == "coordinate_frame"
    )
    assert h7.parameters[8].name == "approx"
    assert len(h7.parameters) == 9

    h7_2 = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        x=1.0,
        rz=0.003,
    )

    print()
    for param in h7_2.parameters:
        print(param.name, param.value)

    assert h7_2.parameters[0].name == "x" and h7_2.parameters[0].value == 1.0
    assert h7_2.parameters[1].name == "rz" and h7_2.parameters[1].value == 0.003
    assert (
        h7_2.parameters[2].name == "convention"
        and h7_2.parameters[2].value == "position_vector"
    )


def test_helmert7param_transformation(source_coordinates):
    """Test the forward transformation of Helmert7Param."""

    h7 = Helmert7Param(
        convention=RotationConvention.COORDINATE_FRAME,
        x=1234.0,
        y=923.0,
        z=523.0,
        rx=0.001,
        ry=0.002,
        rz=0.003,
        s=0.005,
    )

    projstring = "+proj=helmert "
    for param in h7.parameters:
        projstring += f"{param.as_proj_param} "

    print(projstring)
    T = Transformer.from_projstring(projstring)

    transformo_coords = h7.forward(source_coordinates)
    proj_coords = T.transform_many(source_coordinates)

    # We are not going to get an exact match but it's very close and good enough
    assert np.allclose(proj_coords, transformo_coords)

    # Check the inverse transformation
    roundtrip = h7.inverse(transformo_coords)
    assert np.allclose(source_coordinates, roundtrip)


def test_helmert7param_small_angle_approximation():
    """
    Test the rotation matrix with and without the small angles approximation.
    """

    rx = 23.1
    ry = 22.252
    rz = 39.42

    # Check that the rotation matrices are different when produced with
    # and without the small angle approximation. Of course we use sufficiently
    # large rotations for this to be the case.
    helmert_small_angle = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        small_angle_approximation=True,
        rx=rx,
        ry=ry,
        rz=rz,
    )
    helmert_full = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        small_angle_approximation=False,
        rx=rx,
        ry=ry,
        rz=rz,
    )

    assert not np.allclose(helmert_small_angle.R, helmert_full.R)

    # Test specific values of rotation matrices, again with and
    # without the small angles approximation.
    arcsec2rad: float = lambda arcsec: np.deg2rad(arcsec) / 3600.0

    x_rotation_small_angle = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        small_angle_approximation=True,
        rx=rx,
    )

    x_rotation = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        small_angle_approximation=False,
        rx=rx,
    )

    assert x_rotation_small_angle.R[2][1] == arcsec2rad(rx)
    assert x_rotation.R[2][1] != arcsec2rad(rx)


def test_helmert7parameter_estimation(source_coordinates, target_coordinates):
    """
    Verify that estimation of a 7 parameter Helmert works.

    The test is slightly dumb as it simply checks that transformation of the
    source coordinates somewhat matches the target coordinates.
    """
    h = Helmert7Param(
        convention=RotationConvention.POSITION_VECTOR,
        small_angle_approximation=True,
    )

    weights = np.ones_like(source_coordinates)
    h.estimate(source_coordinates, target_coordinates, weights, weights)

    estimated_coordinates = h.forward(source_coordinates)

    assert estimated_coordinates[0, 0] == pytest.approx(target_coordinates[0, 0])
    assert estimated_coordinates[0, 1] == pytest.approx(target_coordinates[0, 1])
    assert estimated_coordinates[0, 2] == pytest.approx(target_coordinates[0, 2])
    assert estimated_coordinates[1, 0] == pytest.approx(target_coordinates[1, 0])
    assert estimated_coordinates[1, 1] == pytest.approx(target_coordinates[1, 1])
    assert estimated_coordinates[1, 2] == pytest.approx(target_coordinates[1, 2])
    assert estimated_coordinates[-1, 0] == pytest.approx(target_coordinates[-1, 0])
    assert estimated_coordinates[-1, 1] == pytest.approx(target_coordinates[-1, 1])
    assert estimated_coordinates[-1, 2] == pytest.approx(target_coordinates[-1, 2])
