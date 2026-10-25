import pathlib

from typing_extensions import Unpack

from runem import (
    JobArgs,
    Options,
    job_function,
    run_command,
)


@job_function
def _job_yarn_deps(
    **kwargs: Unpack[JobArgs],
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
    ]

    run_command(cmd=install_cmd, **kwargs)


@job_function
def _job_prettier(
    **kwargs: Unpack[JobArgs],
) -> None:
    """Runs prettifier on files, including json and maybe yml file.

    TODO: connect me up!
    """
    options: Options = kwargs["options"]
    command_variant = "pretty"
    if options["check-only"]:
        command_variant = "prettyCheck"

    pretty_cmd = [
        "yarn",
        "run",
        command_variant,
    ]

    run_command(cmd=pretty_cmd, **kwargs)
