"""
Presenters that provide statistics on derived transformations.
"""

from numpy._typing._array_like import NDArray


from numpy import intp


from typing import Any, Literal

import numpy as np

from transformo._typing import CoordinateMatrix, ParameterValue
from transformo.core import DataSource, Operator, Presenter

def _estimate_parameters(
    operators: list[Operator],
    source_coordinates: CoordinateMatrix,
    target_coordinates: CoordinateMatrix,
    source_weights: CoordinateMatrix,
    target_weights: CoordinateMatrix,
) -> list[list[ParameterValue]]:
    """
    Helper for the inner loop of `LeaveOneOutPresenter.evaluate()`.

    Return derived parameters from all operators that can estimate
    parameters.
    """

    parameters = []

    current_step_coordinates = source_coordinates
    for operator in operators:
        if operator.can_estimate:
            operator.estimate(
                current_step_coordinates,
                target_coordinates,
                source_weights,
                target_weights,
            )
            parameters.append(operator.parameters)

        current_step_coordinates = operator.forward(current_step_coordinates)

    return parameters

class LeaveOneOutPresenter(Presenter):
    """
    Provide Leave One Out analysis.
    """

    type: Literal["leave_one_out_presenter"] = "leave_one_out_presenter"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        pass

    def as_json(self):
        pass

    def as_markdown(self):
        pass


    def evaluate(
        self,
        operators: list[Operator],
        source_data: DataSource,
        target_data: DataSource,
        results: list[DataSource],
    ) -> None:
        """
        Method

        1. Create hard copies of operators to avoid writing over existing results?
        2. Loop N times, each time leaving one coordinate out
        3. Process all operators, similar to Pipeline.process
        4. Store parameters for each operator that can estimate
        5. ...
        """
        from pprint import pprint

        parameter_groups = []

        N, _ = np.shape(source_data.coordinate_matrix)

        for i in range(N):
            # estimate parameters using all coordinates but the i'th
            idx = np.arange(N) != i
            parameters = _estimate_parameters(
                operators,
                source_data.coordinate_matrix[idx],
                target_data.coordinate_matrix[idx],
                source_data.weights_matrix[idx],
                target_data.weights_matrix[idx],
            )
            parameter_groups.append(parameters)

        parameters = _estimate_parameters(
            operators,
            source_data.coordinate_matrix,
            target_data.coordinate_matrix,
            source_data.weights_matrix,
            target_data.weights_matrix,
        )
        parameter_groups.append(parameters)

        # reorder parameter groups from iteration->step->parameters to step->iteration->parameters

        steps = len(parameter_groups[0])
        data = [[] for _ in range(steps)]
        for group in parameter_groups:
            for step, parameterset in enumerate(group):
                data[step].append([p.value for p in parameterset if p.is_number])


        #pprint(data, width=100, compact=True, )
        for step in data:
            for line in step:
                for number in line:
                    print(f"{number:+9.5f}", end=" ")
                print()
            print("----")

        return


    d = [
        {
            "x": [],
            "y": [],
            "z": [],
        },
        {
            "x": [],
            "y": [],
            "z": [],
            "rx": [],
            ...
        },
    ]
