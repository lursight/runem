import json
import shlex
import typing

from typing_extensions import Unpack

from runem.config_metadata import ConfigMetadata
from runem.run_command import run_command
from runem.types.common import FilePathList
from runem.types.options import OptionsWritable
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import AllKwargs

RUNEM_CTX_PLACEHOLDER = "{runem_ctx}"


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

    # Replace {runem_ctx} with a shell-safe JSON blob of run context (root_dir, etc.).
    if RUNEM_CTX_PLACEHOLDER in command_string:
        root_path = kwargs["root_path"]
        root_dir = kwargs.get("root_dir")
        context: typing.Dict[str, typing.Union[str, bool, float]] = {
            "root_dir": str(root_dir if root_dir is not None else root_path),
        }
        if "run_success" in kwargs:
            context["run_success"] = bool(kwargs["run_success"])
        if "wall_clock_time_saved" in kwargs:
            delta = kwargs["wall_clock_time_saved"]
            context["wall_clock_time_saved"] = delta.total_seconds()
        command_string = command_string.replace(
            RUNEM_CTX_PLACEHOLDER,
            shlex.quote(json.dumps(context, separators=(",", ":"))),
        )

    command_string_files: str = command_string
    if "{file_list}" in command_string:
        file_list: FilePathList = kwargs["file_list"]
        file_list_with_quotes: typing.List[str] = [
            f'"{str(file_path)}"' for file_path in file_list
        ]
        command_string_files = command_string.replace(
            "{file_list}", " ".join(file_list_with_quotes)
        )

    config_metadata: ConfigMetadata = kwargs["config_metadata"]
    options: OptionsWritable = config_metadata.options
    command_string_options: str = command_string_files
    for name, value in options.items():
        # For now, just pass `--option-name`, `--check` or similar to the
        # command line. At some point we will want this to be cleverer, but
        # this will do for now.
        option_search = f"{{{name}}}"
        if option_search in command_string_files:
            replacement = ""
            if value:
                replacement = f"--{name}"
            command_string_options = command_string_options.replace(
                option_search, replacement
            )

    # use shlex to handle parsing of the command string, a non-trivial problem.
    cmd = validate_simple_command(command_string_options)

    # preserve quotes for consistent handling of strings and avoid the "word
    # splitting" problem for unix-like shells.
    cmd_with_quotes = [f'"{token}"' if " " in token else token for token in cmd]

    run_command(cmd=cmd_with_quotes, **kwargs)
