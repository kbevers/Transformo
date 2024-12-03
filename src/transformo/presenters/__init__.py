"""
Transformo Presenter classes.
"""

from __future__ import annotations

from typing import Literal

from py_markdown_table.markdown_table import markdown_table

from transformo.core import DataSource, Operator, Presenter


def construct_markdown_table(header: list[str], rows: list[list[str]]) -> str:
    """
    Present data in tabular form using the Markdown format.

    The number of elements in the header must be equal to the number of
    elements in the individual rows.

    Data is expected as strings. Often numbers will be presented in a
    table. The responsibility of how data is formatted is left to the
    caller.

    Parameters:
        header: Titles for each column in the table
        rows:   Values of cells in table.
    """
    data = [dict(zip(header, row)) for row in rows]

    table = markdown_table(data)
    table.set_params(
        quote=False, padding_width=2, padding_weight="centerright", row_sep="markdown"
    )

    return table.get_markdown()


class DummyPresenter(Presenter):
    """
    A presenter that doesn't do much...
    """

    type: Literal["dummy_presenter"] = "dummy_presenter"

    def evaluate(self, operators: list[Operator], results: list[DataSource]) -> None:
        """
        Evaluate `results` created by `operators`.
        """

    def as_json(self) -> str:
        """
        Present results as JSON.
        """
        return "{}"

    def as_markdown(self) -> str:
        """
        Present result in the markdown text format.
        """
        return "*This section intentionally left blank.*"


# We keept the import's at the end to avoid a circular import. This can be changed
# once `construct_markdown_table` finds a better home outside of this.
# pylint: disable=wrong-import-position
from .coordinates import CoordinatePresenter
from .proj import PROJPresenter

__all__ = [
    "Presenter",
    "DummyPresenter",
    "CoordinatePresenter",
    "PROJPresenter",
]
