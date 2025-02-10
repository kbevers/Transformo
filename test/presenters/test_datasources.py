"""
Tests for DataSourcePresenter.
"""

import json

from transformo.datasources import BerneseCrdDataSource, CsvDataSource
from transformo.presenters import DatasourcePresenter


def test_datasource_presenter(files) -> None:
    """
    Simple sanity tests for the DatasourcePresenter.
    """
    P = DatasourcePresenter(name="Data sources")

    P.evaluate(
        operators=[],
        source_data=BerneseCrdDataSource(
            name="bernie", filename=files["dk_bernese54.CRD"]
        ),
        target_data=CsvDataSource(
            name="commas", filename=files["dk_cors_itrf2014.csv"]
        ),
        results=[],
    )

    presenter_json = json.loads(P.as_json())

    assert "source_data" in presenter_json.keys()
    assert "target_data" in presenter_json.keys()
    assert presenter_json["source_data"][0]["name"] == "bernie"
    assert presenter_json["target_data"][0]["name"] == "commas"

    markdown = P.as_markdown()
    assert markdown.splitlines()[0] == "### Source data"
