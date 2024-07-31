"""
Entry points for the Transformo CLI
"""

import transformo
import transformo.datasources
import transformo.pipeline


def main() -> None:
    """
    The front door of Transformo.
    """
    transformo.logger.info("Hello world!")

    reader1 = transformo.datasources.CsvDataSource(
        r"C:\dev\transformo\test\data\dk_cors_etrs89.csv"
    )
    reader2 = transformo.datasources.CsvDataSource(
        r"C:\dev\transformo\test\data\dk_cors_itrf2014.csv"
    )

    double_reader = reader1 + reader2

    print(double_reader.coordinates)
    print(double_reader.coordinate_matrix)

    pipeline = transformo.pipeline.TransformoPipeline(
        source_data=[reader1, reader2],
        target_data=[reader2],
    )

    print(pipeline)
    print()
    print("=" * 50)
    pipeline_json = pipeline.to_json()
    print(pipeline_json)
    print()

    pipeline_yaml = pipeline.to_yaml()
    print(pipeline_yaml)
    print()
    print("=" * 50)
    # john = transformo.pipeline.TransformoPipeline.model_validate_json(pipeline_json)
    john = transformo.pipeline.TransformoPipeline.from_yaml(pipeline_yaml)
    print()
    print(john)
