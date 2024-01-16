import typing

from runem.run_command import run_command
from runem.types import Options


def _job_prettier(
    **kwargs: typing.Any,
) -> None:
    """Runs prettifier on files, including json and maybe yml file.

    TODO: connect me up!
    """
    options: Options = kwargs["options"]
    command_variant = "pretty"
    if "check_only" in options and options["check_only"]:
        command_variant = "prettyCheck"

    pretty_cmd = [
        "yarn",
        "run",
        command_variant,
    ]

    run_command(cmd=pretty_cmd, **kwargs)
