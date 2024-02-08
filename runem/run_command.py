import os
import pathlib
import typing
from subprocess import PIPE as SUBPROCESS_PIPE
from subprocess import STDOUT as SUBPROCESS_STDOUT
from subprocess import CompletedProcess
from subprocess import run as subprocess_run

from runem.log import log

TERMINAL_WIDTH = 86


class RunCommandBadExitCode(RuntimeError):
    pass


class RunCommandUnhandledError(RuntimeError):
    pass


def get_stdout(process: CompletedProcess[bytes], prefix: str) -> str:
    """Gets stdout from the given process, handling badly configured process objects.

    Additionally prefixes each line of the output with a label.
    """
    stdout: str
    try:
        stdout = str(process.stdout.decode("utf-8"))
    except UnboundLocalError:
        stdout = "No process started, does it exist?"
    stdout = prefix + stdout.replace("\n", f"\n{prefix}")
    return stdout


def _prepare_environment(
    env_overrides: typing.Optional[typing.Dict[str, str]],
) -> typing.Dict[str, str]:
    """Returns a consolidated environment merging os.environ and overrides."""
    # first and always, copy in the environment
    run_env: typing.Dict[str, str] = {
        **os.environ,  # copy in the environment
    }
    if env_overrides:
        # overload the os.environ with overrides
        run_env.update(env_overrides)
    return run_env


def _log_command_execution(
    cmd_string: str,
    label: str,
    env_overrides: typing.Optional[typing.Dict[str, str]],
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]],
    verbose: bool,
) -> None:
    """Logs out useful debug information on '--verbose'."""
    if verbose:
        log(f"running: start: {label}: {cmd_string}")
        if valid_exit_ids is not None:
            valid_exit_strs = ",".join(str(exit_code) for exit_code in valid_exit_ids)
            log(f"\tallowed return ids are: {valid_exit_strs}")

    if verbose:
        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            log(f"ENV OVERRIDES: {env_overrides_as_string} {cmd_string}")


def run_command(
    cmd: typing.List[str],  # 'cmd' is the only thing that can't be optionally kwargs
    label: str,
    verbose: bool,
    env_overrides: typing.Optional[typing.Dict[str, str]] = None,
    ignore_fails: bool = False,
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]] = None,
    cwd: typing.Optional[pathlib.Path] = None,
    **kwargs: typing.Any,
) -> str:
    """Runs the given command, returning stdout or throwing on any error."""
    cmd_string = " ".join(cmd)

    run_env: typing.Dict[str, str] = _prepare_environment(
        env_overrides,
    )
    _log_command_execution(
        cmd_string,
        label,
        env_overrides,
        valid_exit_ids,
        verbose,
    )

    if valid_exit_ids is None:
        valid_exit_ids = (0,)

    # init the process in case it throws for things like not being able to
    # convert the command to a list of strings.
    process: typing.Optional[CompletedProcess[bytes]] = None
    try:
        process = subprocess_run(
            cmd,
            check=False,  # Do NOT throw on non-zero exit
            env=run_env,
            stdout=SUBPROCESS_PIPE,
            stderr=SUBPROCESS_STDOUT,
            cwd=cwd,
        )
        if process.returncode not in valid_exit_ids:
            valid_exit_strs = ",".join([str(exit_code) for exit_code in valid_exit_ids])
            raise RunCommandBadExitCode(
                (
                    f"non-zero exit {process.returncode} (allowed are "
                    f"{valid_exit_strs}) from {cmd_string}"
                )
            )
    except BaseException as err:
        if ignore_fails:
            return ""
        stdout: str = get_stdout(process, prefix=f"{label}: ERROR: ") if process else ""
        env_overrides_as_string = ""
        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            env_overrides_as_string = f"{env_overrides_as_string} "
        error_string = (
            f"runem: test: FATAL: command failed: {label}"
            f"\n\t{env_overrides_as_string}{cmd_string}"
            f"\nERROR"
            f"\n{str(stdout)}"
            f"\nERROR END"
        )

        if isinstance(err, RunCommandBadExitCode):
            raise RunCommandBadExitCode(error_string) from err
        # fallback to raising a RunCommandUnhandledError
        raise RunCommandUnhandledError(error_string) from err

    assert process is not None
    cmd_stdout: str = get_stdout(process, prefix=f"{label}: ")
    if verbose:
        log(cmd_stdout)
        log(f"running: done: {label}: {cmd_string}")
    return cmd_stdout
