"""
Transformo writer classes.
"""

from typing import Protocol


class TransformoWriter(Protocol):
    """Base writer class."""

    def __init__(self) -> None:
        """Set up base writer"""
