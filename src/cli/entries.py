"""
Entry points for the Transformo CLI
"""

import click

import transformo
import transformo.datasources
import transformo.pipeline


@click.command()
@click.version_option(transformo.__version__)
@click.argument("configuration-file", type=click.Path(exists=True))
def main(configuration_file: click.Path) -> None:
    """
    The  front door of Transformo.

    At this point in time this takes a configuration file that defines a pipeline
    in YAML format.

    This application is under development and can be expected to change in the future.
    """
    with open(configuration_file, "r", encoding="utf-8") as yaml:
        pipeline = transformo.pipeline.TransformoPipeline.from_yaml(yaml.read())

    pipeline.process()
    print(pipeline.results_as_text())
