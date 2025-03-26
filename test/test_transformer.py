"""
...
"""

import numpy as np

from transformo.transformer import Transformer


def test_initialization() -> None:
    """
    ...
    """
    t = Transformer()

    result = t.transform_many([(1, 2, 3), (4, 5, 6)])

    assert result[0][1] == 2
    assert result.shape == (2, 3)


def test_transform_many() -> None:
    "Test the transform_many method"
    t = Transformer.from_projstring("+proj=helmert +x=1000")

    matrix = np.array(
        [
            (1, 2, 3),
            (4, 5, 6),
            (7, 8, 9),
        ]
    )

    result = t.transform_many(matrix)

    assert result.shape == matrix.shape
    assert np.all(result[:, 0] > 1000)


def test_transform_one() -> None:
    "Test the transform_one method"

    t = Transformer.from_projstring("+proj=helmert +y=500")
    result = t.transform_one((4, 5, 6))

    assert result[1] == 505
    assert result.shape == (3,)
