"""
Tests of basic data structures like `Coordinate`.
"""

import numpy as np
import pytest

from transformo.datatypes import Coordinate, Parameter


def test_coordinate_from_str():
    """Test class method Coordinate.from_str()"""

    c = Coordinate.from_str(
        "BUDP",
        "2018.24",
        "3522395.52810",
        "933244.47970",
        "5217231.27310",
        "1.0",
        "1.0",
        "1.0",
        "1.0",
    )

    assert c.station == "BUDP"
    assert c.t == 2018.24
    assert c.x == 3522395.52810
    assert c.y == 933244.47970
    assert c.z == 5217231.27310
    assert c.sx == 1.0
    assert c.sy == 1.0
    assert c.sz == 1.0
    assert c.w == 1.0

    # ... and for good measure, a few checks to verify that pydantic does what it is meant to do
    with pytest.raises(ValueError):
        c = Coordinate.from_str(
            "5234",
            "not-a-number",
            "not-a-number",
            "not-a-number",
            "not-a-number",
            "also-not-a-number",
            "also-not-a-number",
            "also-not-a-number",
            "also-not-a-number",
        )

    with pytest.raises(ValueError):
        c = Coordinate.from_str(
            5234,
            "123",
            "234",
            "345",
            "456",
            "1",
            "1",
            "1",
            "1",
        )


def test_coordinate_vector_property(coordinate: Coordinate):
    """Test vector property of Coordinate"""

    assert coordinate.vector[0] == coordinate.x
    assert coordinate.vector[1] == coordinate.y
    assert coordinate.vector[2] == coordinate.z

    assert isinstance(coordinate.vector, np.ndarray)


def test_coordinate_weights_property(coordinate: Coordinate):
    """Test vector property of Coordinate"""

    assert coordinate.weights[0] == 1 / coordinate.sx * coordinate.w
    assert coordinate.weights[1] == 1 / coordinate.sy * coordinate.w
    assert coordinate.weights[2] == 1 / coordinate.sz * coordinate.w

    assert isinstance(coordinate.weights, np.ndarray)


def test_parameter():
    """Test functionality of Parameter"""

    proj_parameter = Parameter("proj", "helmert")
    assert proj_parameter.is_flag is False
    assert proj_parameter.as_proj_param == "+proj=helmert"

    flag_parameter = Parameter("step")
    assert flag_parameter.is_flag is True
    assert flag_parameter.as_proj_param == "+step"

    plus_flag_parameter = Parameter("+step")
    assert plus_flag_parameter.is_flag is True
    assert plus_flag_parameter.as_proj_param == "+step"

    float_parameter = Parameter("float", 123.432)
    assert float_parameter.is_flag is False
    assert float_parameter.as_proj_param == "+float=123.432"
