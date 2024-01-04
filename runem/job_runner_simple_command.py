import shlex
import typing

from runem.run_command import run_command
from runem.types import JobConfig


def job_runner_simple_command(
    **kwargs: typing.Any,
) -> None:
    """Parses the command and tries to run it via the system.

    Commands inherit the environment.
    """
    # assume we have the job.command entry, allowing KeyError to propagate up
    job_config: JobConfig = kwargs["job"]
    command_string: str = job_config["command"]

    # use shlex to handle parsing of the command string, a non-trivial problem.
    result = shlex.split(command_string)

    # preserve quotes for consistent handling of strings and avoid the "word
    # splitting" problem for unix-like shells.
    result_with_quotes = [f'"{token}"' if " " in token else token for token in result]

    run_command(cmd=result_with_quotes, **kwargs)
