"""
Tests for statistics Presenters
"""

from transformo.datasources import CsvDataSource
from transformo.operators import (
    Helmert3Param,
    Helmert7Param,
    RotationConvention,
    ProjOperator,
)
from transformo.presenters import LeaveOneOutPresenter
from transformo.presenters.statistics import _estimate_parameters

def test_estimate_parameters(files):
    operators = [
        ProjOperator(proj_string="+proj=noop"),
        Helmert3Param(),
        Helmert7Param(convention=RotationConvention.COORDINATE_FRAME),
        ProjOperator(proj_string="+proj=noop"),
    ]
    source_data = CsvDataSource(filename=files["dk_cors_etrs89.csv"])
    target_data = CsvDataSource(filename=files["dk_cors_itrf2014.csv"])

    parameters = _estimate_parameters(
        operators,
        source_data.coordinate_matrix,
        target_data.coordinate_matrix,
        source_data.weights_matrix,
        target_data.weights_matrix,
    )

    for n, paramlist in enumerate(parameters):
        print(f"step {n}:")
        for p in paramlist:
            print(f"  {p.name}, {p.value}")

    assert len(parameters) == 2
    assert len(parameters[0]) == 3
    assert len(parameters[1]) == 8 # rotation convention + 7 helmert params

    assert False



def test_leave_one_out_presenter(files):
    p = LeaveOneOutPresenter()

    assert isinstance(p, LeaveOneOutPresenter)


    p.evaluate(
        operators=[
            ProjOperator(proj_string="+proj=noop"),
            Helmert3Param(),
            Helmert7Param(convention=RotationConvention.COORDINATE_FRAME),
            ProjOperator(proj_string="+proj=noop"),
        ],
        source_data=CsvDataSource(name="bernie", filename=files["dk_cors_etrs89.csv"]),
        target_data=CsvDataSource(
            name="commas", filename=files["dk_cors_itrf2014.csv"]
        ),
        results=[],
    )

    assert False
