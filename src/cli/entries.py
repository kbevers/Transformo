"""
Entry points for the Transformo CLI.
"""

import importlib.resources
import logging
import warnings
from pathlib import Path

import click
import pandoc
from rich.console import Console
from rich.markdown import Markdown

import transformo
import transformo.datasources
from transformo.pipeline import Pipeline

# The Python pandoc package complains that the pandoc binary is too new,
# we suppress that warning in
warnings.filterwarnings("ignore", category=UserWarning, module="pandoc")

# Set up logger
logger = logging.getLogger("transformo")


@click.command()
@click.version_option(transformo.__version__)
@click.argument("configuration-file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--report-in-terminal",
    is_flag=True,
    default=False,
    help="Print report directly to the terminal.",
)
@click.option(
    "--markdown",
    is_flag=True,
    default=False,
    help="Output report with results in Markdown-format.",
)
@click.option(
    "--html",
    is_flag=True,
    default=False,
    help="Output report with results in HTML-format.",
)
@click.option(
    "--pdf",
    is_flag=True,
    default=False,
    help="Output report with results in PDF-format.",
)
@click.option(
    "--out-dir",
    default="transformo_results",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Directory where generated files are placed. Defaults to `transformo_results` placed in the current working directory.",
)
def main(
    configuration_file: click.Path,
    report_in_terminal: bool,
    markdown: bool,
    html: bool,
    pdf: bool,
    out_dir: Path,
) -> None:
    """
    The front door of Transformo.

    At this point in time this takes a configuration file that defines a pipeline
    in YAML format.

    Files generated by Transformo are placed in the folder `output`. Existing files
    will be overwritten.

    This application is under development and can be expected to change in the future.
    """

    with open(configuration_file, "r", encoding="utf-8") as yaml:
        pipeline = Pipeline.from_yaml(yaml.read())

    pipeline.process()
    markdown_results = pipeline.results_as_markdown()

    # output to terminal
    if report_in_terminal:
        console = Console()
        console.print(Markdown(markdown_results, justify="left"))

    # we end the program here if there's no output files to write
    if not (markdown or html or pdf):
        if not report_in_terminal:
            logger.warning("Pipeline processed but results not shown or saved to disk")
        raise SystemExit

    # output to filesystem
    out_dir.mkdir(parents=True, exist_ok=True)

    if markdown:
        with open(out_dir / "transformo.md", "w", encoding="utf-8") as md_file:
            md_file.writelines(markdown_results)

    if html:
        resource_file_dir = importlib.resources.files("cli")
        css_file = str(resource_file_dir) / Path("style.css")
        try:
            pandoc.write(
                pandoc.read(markdown_results),
                format="html",
                file=out_dir / "transformo.html",
                options=["--standalone", "--embed-resources", "--css", css_file],
            )
        except PermissionError:
            logger.error(
                "Can't write HTML file. Perhaps a file with the same name is open?"
            )
            raise SystemExit(1)

    if pdf:
        try:
            pandoc.write(
                pandoc.read(markdown_results),
                format="pdf",
                file=out_dir / "transformo.pdf",
            )
        except PermissionError:
            logger.error(
                "Can't write PDF file. Perhaps a file with the same name is open?"
            )
            raise SystemExit(1)
