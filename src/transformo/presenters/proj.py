"""
PROJ-based Presenters.
"""

from __future__ import annotations

import json
from typing import Literal

from transformo.core import DataSource, Operator, Presenter


class PROJPresenter(Presenter):
    """
    Present parameters as a PROJ string.

    Possible future usefull settings:
        - Number of decimal places for floats.
    """

    type: Literal["proj_presenter"] = "proj_presenter"

    def __init__(self, **kwargs) -> None:
        """."""
        super().__init__(**kwargs)

        self._output: dict[str, str] = {}

    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        """
        Parse parameters from `operators`.

        Ignores contents of `results`.
        """
        steps = []
        for operator in operators:
            if operator.proj_operation_name == "noop":
                continue

            projstr = f"+proj={operator.proj_operation_name}"
            for param in operator.parameters:
                projstr += f" {param.as_proj_param}"

            # if `projstr` is a PROJ pipeline definition we need to manipulate
            # it a bit to avoid nested pipelines (which is not allowed in PROJ)
            steps.append(projstr.removeprefix("+proj=pipeline +step").lstrip())

        if len(steps) == 0:
            self._output["projstring"] = "+proj=noop"
            return

        if len(steps) == 1:
            self._output["projstring"] = steps[0]
            return

        self._output["projstring"] = "+proj=pipeline +step " + " +step ".join(steps)

    def as_json(self) -> str:
        """
        Return PROJstring as a JSON string.

        Use the key "projstring" to access the PROJstring.
        """
        return json.dumps(self._output)

    def as_markdown(self) -> str:
        """Return PROJstring as text."""
        params = json.loads(self.as_json())
        txt = params["projstring"]
        formatted_projstring = txt.replace(" +step", "\n  +step").strip()

        markdown = f"""
Transformation parameters given as a [PROJ](https://proj.org/) string.
```
{formatted_projstring}
```
""".strip()

        return markdown
