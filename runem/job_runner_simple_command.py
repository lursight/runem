import shlex
import typing

from typing_extensions import Unpack

from runem.run_command import run_command
from runem.types.common import FilePathList
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import AllKwargs


def validate_simple_command(command_string: str) -> typing.List[str]:
    """Use shlex to handle parsing of the command string, a non-trivial problem."""
    split_command: typing.List[str] = shlex.split(command_string)
    return split_command


def job_runner_simple_command(
    **kwargs: Unpack[AllKwargs],
) -> None:
    """Parses the command and tries to run it via the system.

    Commands inherit the environment.
    """
    # assume we have the job.command entry, allowing KeyError to propagate up
    job_config: JobConfig = kwargs["job"]
    command_string: str = job_config["command"]

    command_string_files: str = command_string
    if "{file_list}" in command_string:
        file_list: FilePathList = kwargs["file_list"]
        file_list_with_quotes: typing.List[str] = [
            f'"{str(file_path)}"' for file_path in file_list
        ]
        command_string_files = command_string.replace(
            "{file_list}", " ".join(file_list_with_quotes)
        )

    # use shlex to handle parsing of the command string, a non-trivial problem.
    cmd = validate_simple_command(command_string_files)

    # preserve quotes for consistent handling of strings and avoid the "word
    # splitting" problem for unix-like shells.
    cmd_with_quotes = [f'"{token}"' if " " in token else token for token in cmd]

    run_command(cmd=cmd_with_quotes, **kwargs)
