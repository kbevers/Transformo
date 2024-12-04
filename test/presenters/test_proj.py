"""
Tests for transformo.presenters.proj
"""

from transformo.operators import DummyOperator, HelmertTranslation, ProjOperator
from transformo.presenters import PROJPresenter


def test_proj_presenter():
    """
    Test that the PROJPresenter can return a proper PROJstring.
    """

    # Operators
    dummy = DummyOperator()
    helmert = HelmertTranslation()
    helmert_with_params = HelmertTranslation(x=3.42, y=534.533, z=1234.5678)
    helmert_with_one_params = HelmertTranslation(y=432.52)
    proj_with_pipeline = ProjOperator(
        proj_string="+proj=pipeline +step +proj=cart +inv +step +proj=utm +zone=32"
    )

    presenter_with_no_operators = PROJPresenter()
    presenter_with_no_operators.evaluate(operators=[], results=[])

    assert presenter_with_no_operators.as_json() == '{"projstring": "+proj=noop"}'

    presenter_with_one_operator = PROJPresenter()
    presenter_with_one_operator.evaluate(operators=[helmert], results=[])
    assert presenter_with_one_operator.as_json() == '{"projstring": "+proj=noop"}'

    presenter_with_several_operators = PROJPresenter()
    presenter_with_several_operators.evaluate(
        operators=[dummy, helmert_with_one_params, helmert_with_params], results=[]
    )

    expected_pipeline = (
        "+proj=pipeline +step "
        "+proj=helmert +y=432.52 +step "
        "+proj=helmert +x=3.42 +y=534.533 +z=1234.5678"
    )
    assert (
        presenter_with_several_operators.as_json()
        == f'{{"projstring": "{expected_pipeline}"}}'
    )

    expected_pipeline = """
Transformation parameters given as a [PROJ](https://proj.org/) string.
```
+proj=pipeline
  +step +proj=helmert +y=432.52
  +step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678
```
""".strip()

    print(presenter_with_several_operators.as_markdown())
    assert presenter_with_several_operators.as_markdown() == expected_pipeline

    # Test that nested PROJ pipelines are handled correctly
    presenter_with_several_proj_pipeline_operators = PROJPresenter()
    presenter_with_several_proj_pipeline_operators.evaluate(
        operators=[
            dummy,
            helmert_with_one_params,
            proj_with_pipeline,
            helmert_with_params,
            proj_with_pipeline,
        ],
        results=[],
    )
    expected_pipeline = (
        "+proj=pipeline "
        "+step +proj=helmert +y=432.52 "
        "+step +proj=cart +inv +step +proj=utm +zone=32 "
        "+step +proj=helmert +x=3.42 +y=534.533 +z=1234.5678 "
        "+step +proj=cart +inv +step +proj=utm +zone=32"
    )
    assert (
        presenter_with_several_proj_pipeline_operators.as_json()
        == f'{{"projstring": "{expected_pipeline}"}}'
    )
