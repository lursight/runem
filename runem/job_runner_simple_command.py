import json
import shlex
import typing
from pathlib import Path

from typing_extensions import Unpack

from runem.hook.hook_args import HookArgs
from runem.job.job_args import JobArgs
from runem.job.job_function import job_function
from runem.run_command import run_command
from runem.types.common import FilePathList
from runem.types.options import OptionsWritable
from runem.types.runem_config import JobConfig

if typing.TYPE_CHECKING:
    from runem.config_metadata import ConfigMetadata

RUNEM_CTX_PLACEHOLDER = "{runem_ctx}"


def _validate_simple_command(command_string: str) -> typing.List[str]:
    """Use shlex to handle parsing of the command string, a non-trivial problem."""
    split_command: typing.List[str] = shlex.split(command_string)
    return split_command


def _placeholder_ctx(
    command_string: str,
    metadata: HookArgs.HookData | None,
    root_path: Path,
) -> str:
    """Replace {runem_ctx} th a shell-safe JSON blob of run context

    Args:
        command_string: the job's command string
        metadata: the job invocation metadata if any
        root_path: the main project root-path

    Returns:
        Returns the modified command_string
    """
    assert RUNEM_CTX_PLACEHOLDER in command_string

    # Always add the `root_path` context
    context: typing.Dict[str, typing.Union[str, bool, float]] = {
        "root_path": str(root_path),
    }
    if metadata is not None:
        run_success = metadata.get("run_success")
        if isinstance(run_success, bool):
            context["run_success"] = run_success
        if "wall_clock_time_saved_s" in metadata:
            wall_clock_time_saved_s = metadata.get("wall_clock_time_saved_s")
            assert isinstance(wall_clock_time_saved_s, float)
            context["wall_clock_time_saved_s"] = wall_clock_time_saved_s
    command_string = command_string.replace(
        RUNEM_CTX_PLACEHOLDER,
        shlex.quote(json.dumps(context, separators=(",", ":"))),
    )
    return command_string


def _placeholder_file_list(
    command_string: str,
    **kwargs: Unpack[JobArgs],
) -> str:
    if "{file_list}" in command_string:
        job_kwargs: JobArgs = kwargs
        file_list: FilePathList = job_kwargs["file_list"]
        file_list_with_quotes: typing.List[str] = [
            f'"{str(file_path)}"' for file_path in file_list
        ]
        command_string = command_string.replace(
            "{file_list}", " ".join(file_list_with_quotes)
        )
    return command_string


def _placeholder_metadata(
    command_string: str,
    metadata: HookArgs.HookData,
) -> str:
    if "{metadata}" in command_string:
        command_string = command_string.replace(
            "{metadata}",
            shlex.quote(json.dumps(metadata, separators=(",", ":"))),
        )
    for name, value in metadata.items():
        # For now, just pass `--option-name`, `--check` or similar to the
        # command line. At some point we will want this to be cleverer, but
        # this will do for now.
        meta_search: str = f"{{{name}}}"
        if meta_search in command_string:
            replacement = f"{value}"
            command_string = command_string.replace(meta_search, replacement)
    return command_string


def _resolve_placeholders(
    command_string: str,
    **kwargs: Unpack[JobArgs],
) -> str:
    """Replaces `{<var>}` placeholders with the data kwargs.

    Args:
        command_string: The string e.g. `ls {file_list}`
        kwargs: The type-specific kwargs that this job/task/hook is invoked with.

    Returns:
        The command_string with all `{<var>}` placeholders replaced.
    """
    metadata: HookArgs.HookData | None = kwargs.get("metadata")

    if RUNEM_CTX_PLACEHOLDER in command_string:
        root_path: Path = kwargs["root_path"]
        command_string = _placeholder_ctx(command_string, metadata, root_path)

    if "file_list" in kwargs:
        command_string = _placeholder_file_list(command_string, **kwargs)

    if metadata is not None:
        command_string = _placeholder_metadata(command_string, metadata)

    config_metadata: "ConfigMetadata" = kwargs["config_metadata"]
    options: OptionsWritable = config_metadata.options
    for name, value in options.items():
        # For now, just pass `--option-name`, `--check` or similar to the
        # command line. At some point we will want this to be cleverer, but
        # this will do for now.
        option_search: str = f"{{{name}}}"
        if option_search in command_string:
            replacement = ""
            if value:
                replacement = f"--{name}"
            command_string = command_string.replace(option_search, replacement)
    return command_string


@job_function
def job_runner_simple_command(
    **kwargs: Unpack[JobArgs],
) -> None:
    """Parses the command and tries to run it via the system.

    Commands inherit the environment.
    """
    # assume we have the job.command entry, allowing KeyError to propagate up
    job_config: JobConfig = kwargs["job"]
    command_string: typing.Optional[str] = job_config.get("command", None)
    if command_string is None:
        raise RuntimeError(
            "invalid invocation of job_runner_simple_command without 'command'!"
        )

    command_string = _resolve_placeholders(command_string, **kwargs)

    # use shlex to handle parsing of the command string, a non-trivial problem.
    cmd = _validate_simple_command(command_string)

    # preserve quotes for consistent handling of strings and avoid the "word
    # splitting" problem for unix-like shells.
    cmd_with_quotes = [f'"{token}"' if " " in token else token for token in cmd]

    run_command(cmd=cmd_with_quotes, **kwargs)
