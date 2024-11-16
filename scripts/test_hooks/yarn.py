import pathlib
import typing

from runem.run_command import run_command
from runem.types import Options, OptionsWritable


def _job_yarn_deps(
    **kwargs: typing.Any,
) -> None:
    """Installs the yarn deps."""
    options: Options = kwargs["options"]

    install_requested = options["install-deps"]
    if not (install_requested):
        root_path: pathlib.Path = kwargs["root_path"]
        if (root_path / "node_modules").exists():
            # An install was not requested, nor required.
            return

    install_cmd = [
        "yarn",
        "install",
        "--immutable",
    ]

    run_command(cmd=install_cmd, **kwargs)


def _job_prettier(
    **kwargs: typing.Any,
) -> None:
    """Runs prettifier on files, including json and maybe yml file.

    TODO: connect me up!
    """
    options: OptionsWritable = kwargs["options"]
    command_variant = "pretty"
    if options["check-only"]:
        command_variant = "prettyCheck"

    pretty_cmd = [
        "yarn",
        "run",
        command_variant,
    ]

    run_command(cmd=pretty_cmd, **kwargs)
