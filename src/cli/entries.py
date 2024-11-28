"""
Entry points for the Transformo CLI.
"""

import click
from rich.console import Console
from rich.markdown import Markdown

import transformo
import transformo.datasources
from transformo.pipeline import Pipeline


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
        pipeline = Pipeline.from_yaml(yaml.read())

    pipeline.process()

    console = Console()
    markdown = Markdown(pipeline.results_as_markdown(), justify="left")
    console.print(markdown)
