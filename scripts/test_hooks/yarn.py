import typing

from runem.run_command import run_command
from runem.types import OptionsWritable


def _job_prettier(
    **kwargs: typing.Any,
) -> None:
    """Runs prettifier on files, including json and maybe yml file.

    TODO: connect me up!
    """
    options: OptionsWritable = kwargs["options"]
    command_variant = "pretty"
    if "check-only" in options and options["check-only"]:
        command_variant = "prettyCheck"

    pretty_cmd = [
        "yarn",
        "run",
        command_variant,
    ]

    run_command(cmd=pretty_cmd, **kwargs)
