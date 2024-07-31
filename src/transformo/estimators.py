"""
Transformo estimator classes.
"""

from typing import Protocol


class TransformoEstimator(Protocol):
    """Base estimator class."""

    def __init__(self) -> None:
        """Set up base estimator"""
