"""
Transformo - The general purpose tool for determining geodetic transformations
"""

from __future__ import annotations

import asyncio
import logging

__version__ = "0.1.0"

# Logging
console_handler = logging.StreamHandler()
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)
logger.setLevel(logging.WARNING)


# The functions below are all related to running shell commands. It may
# seem overly complicated but there does not seem to be a simpler way to
# capture the STDOUT and STDERR seperately.


async def _log_warning(stream):
    while not stream.at_eof():
        data = await stream.readline()
        line = data.decode("ascii").rstrip()
        logger.warning(line)


async def _log_error(stream):
    while not stream.at_eof():
        data = await stream.readline()
        line = data.decode("ascii").rstrip()
        logger.error(line)


async def _execute(command, *argument):
    proc = await asyncio.create_subprocess_exec(
        command,
        *argument,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    tasks = [
        asyncio.create_task(_log_warning(proc.stdout)),
        asyncio.create_task(_log_error(proc.stderr)),
        asyncio.create_task(proc.wait()),
    ]
    await asyncio.wait(tasks)

    return proc.returncode


def run_command(command: str):
    """Run a command.

    Stdout and stderr utput of command is logged at WARNING and ERROR
    levels respectively.
    """
    cmd = command.split()
    asyncio.run(_execute(cmd[0], *cmd[1:]))
