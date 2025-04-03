"""
Tests of basic data structures like `Coordinate`.
"""

import numpy as np
import pydantic
import pytest

from transformo.datatypes import Coordinate, Parameter
from transformo.transformer import Transformer


def test_coordinate_field_limits():
    """Test the various limits set on the Coordinate fields."""

    def parameters(**kwargs):
        """Override one or more sensible default parameters"""
        params = {
            "station": "TEST",
            "t": 2025.0,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "sx": 0.0,
            "sy": 0.0,
            "sz": 0.0,
            "w": 1.0,
        }

        for key, value in kwargs.items():
            params[key] = value

        return params

    assert isinstance(Coordinate(**parameters()), Coordinate)

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(t=-2000.0))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(w=-1.0))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(w=np.nan))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(w=np.inf))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(sx=-1.0))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(sy=-1.0))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(sz=-1.0))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(sx=np.nan))

    with pytest.raises(pydantic.ValidationError):
        Coordinate(**parameters(sx=np.inf))


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

    # ... and for good measure, a few checks to verify that
    # pydantic does what it is meant to do
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

    assert coordinate.weights[0] == 1 / coordinate.sx**2 * coordinate.w
    assert coordinate.weights[1] == 1 / coordinate.sy**2 * coordinate.w
    assert coordinate.weights[2] == 1 / coordinate.sz**2 * coordinate.w

    assert isinstance(coordinate.weights, np.ndarray)


def test_coordinate_geojson_feature(coordinate: Coordinate):
    """Test geojson_feature returns valid GeoJSON features."""

    feature = coordinate.geojson_feature()

    print(feature)

    assert feature["geometry"]["coordinates"][0] == coordinate.x
    assert feature["geometry"]["coordinates"][1] == coordinate.y
    assert feature["properties"]["station"] == coordinate.station

    # Check that adding auxillary properties works
    feature_with_properties = coordinate.geojson_feature(
        properties={
            "E": 12.3,
            "N": 4.32,
            "U": 6.23,
            "attribute": "value",
            "station": "STATION",
        }
    )

    assert feature_with_properties["properties"]["E"] == 12.3
    assert feature_with_properties["properties"]["N"] == 4.32
    assert feature_with_properties["properties"]["U"] == 6.23
    assert feature_with_properties["properties"]["attribute"] == "value"

    # verify that origin properties are overriden by those in `properties`
    assert feature_with_properties["properties"]["station"] == "STATION"

    # test that the transformer works on the output coordinates
    transformer = Transformer.from_projstring("+proj=helmert +x=1.0 +y=2.0")
    feature_transformed_coords = coordinate.geojson_feature(transformer=transformer)

    assert (
        feature_transformed_coords["geometry"]["coordinates"][0] == coordinate.x + 1.0
    )
    assert (
        feature_transformed_coords["geometry"]["coordinates"][1] == coordinate.y + 2.0
    )


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
