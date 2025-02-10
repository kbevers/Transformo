"""
Presenters related to DataSource's.
"""

from __future__ import annotations

import json
from typing import Literal

import yaml

from transformo.core import DataSource, Operator, Presenter


class DatasourcePresenter(Presenter):
    """
    Create lists of datasources used in a pipeline.
    """

    type: Literal["datasource_presenter"] = "datasource_presenter"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, list] = {
            "source_data": [],
            "target_data": [],
        }

    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        # for datasource in source_data.origins:
        for datasource in source_data.origins:
            self._data["source_data"].append(
                datasource.model_dump(exclude_unset=True, mode="json")
            )

        for datasource in target_data.origins:
            self._data["target_data"].append(
                datasource.model_dump(exclude_unset=True, mode="json")
            )

    def as_json(self):
        return json.dumps(self._data)

    def as_markdown(self):
        sources = yaml.dump(self._data["source_data"], sort_keys=False)
        targets = yaml.dump(self._data["target_data"], sort_keys=False)

        return f"""\
### Source data
```yaml
{sources}
```

### Target data
```yaml
{targets}
```
"""
