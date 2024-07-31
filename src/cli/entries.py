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
        r"C:\dev\transformo\test\csvfile.csv"
    )
    reader2 = transformo.datasources.CsvDataSource(
        r"C:\dev\transformo\test\csvfile.csv"
    )

    double_reader = reader1 + reader2

    print(double_reader.coordinates)
    print(double_reader.coordinate_matrix)

    # transformo.pipeline.DatasourceConfig.check_valid_name("CsvDataSource")
    # transformo.pipeline.DatasourceConfig.check_valid_name("DataSource")

    pipeline = transformo.pipeline.TransformoPipeline([reader1], [reader2])

    print(pipeline)
