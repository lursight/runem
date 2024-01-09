import os
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
    stdout = stdout.replace("\n", f"\n{prefix}")
    return stdout


def run_command(  # noqa: C901 # pylint: disable=too-many-branches
    cmd: typing.List[str],  # 'cmd' is the only thing that can't be optionally kwargs
    label: str,
    verbose: bool,
    env_overrides: typing.Optional[typing.Dict[str, str]] = None,
    ignore_fails: bool = False,
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]] = None,
    **kwargs: typing.Any,
) -> str:
    """Runs the given command, returning stdout or throwing on any error."""
    cmd_string: str = " ".join(cmd)
    if verbose:
        log(f"running: start: {label}: {cmd_string}")
        if valid_exit_ids is not None:
            valid_exit_strs = ",".join([str(exit_code) for exit_code in valid_exit_ids])
            log(f"\tallowed return ids are: {valid_exit_strs}")

    if valid_exit_ids is None:
        valid_exit_ids = (0,)

    # create a new env with overrides
    run_env: typing.Dict[str, str] = {"LANG_DO_PRINTS": "False"}

    if verbose:
        run_env = {"LANG_DO_PRINTS": "True"}

    if verbose:
        run_env_as_string = " ".join(
            [f"{key}='{value}'" for key, value in run_env.items()]
        )
        log(f"RUN ENV OVERRIDES: {run_env_as_string } {cmd_string}")

        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            log(f"ENV OVERRIDES: {env_overrides_as_string} {cmd_string}")

    env_overrides_dict = {}
    if env_overrides:
        env_overrides_dict = env_overrides
    # merge the overrides into the env
    run_env = {
        **run_env,
        **os.environ.copy(),
        **env_overrides_dict,
    }

    run_env_param: typing.Optional[typing.Dict[str, str]] = None
    if run_env:  # pragma: FIXME: add code coverage
        run_env_param = run_env

    # init the process in case it throws for things like not being able to
    # convert the command to a list of strings.
    process: typing.Optional[CompletedProcess[bytes]] = None
    try:
        process = subprocess_run(
            cmd,
            check=False,  # Do NOT throw on non-zero exit
            env=run_env_param,
            stdout=SUBPROCESS_PIPE,
            stderr=SUBPROCESS_STDOUT,
        )  # raise on non-zero
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
            f"\n\t{str(stdout)}"
            f"\nERROR END"
        )

        if isinstance(err, RunCommandBadExitCode):
            raise RunCommandBadExitCode(error_string) from err
        # fallback to raising a RunCommandUnhandledError
        raise RunCommandUnhandledError(error_string) from err

    assert process is not None
    cmd_stdout: str = get_stdout(process, prefix=label)
    if verbose:
        log(cmd_stdout)
        log(f"running: done: {label}: {cmd_string}")
    return cmd_stdout
