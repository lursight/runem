import os
import pathlib
import typing
from datetime import timedelta
from subprocess import PIPE as SUBPROCESS_PIPE
from subprocess import STDOUT as SUBPROCESS_STDOUT
from subprocess import Popen
from timeit import default_timer as timer

from runem.log import log

TERMINAL_WIDTH = 86


class RunCommandBadExitCode(RuntimeError):
    pass


class RunCommandUnhandledError(RuntimeError):
    pass


# A function type for recording timing information.
RecordSubJobTimeType = typing.Callable[[str, timedelta], None]


def parse_stdout(stdout: str, prefix: str) -> str:
    """Prefixes each line of the output with a given label, except trailing new
    lines."""
    # Edge case: Return the prefix immediately for an empty string
    if not stdout:
        return prefix

    # Split stdout into lines, noting if it ends with a newline
    ends_with_newline = stdout.endswith("\n")
    lines = stdout.split("\n")

    # Apply prefix to all lines except the last if it's empty (due to a trailing newline)
    modified_lines = [f"{prefix}{line}" for line in lines[:-1]] + (
        [lines[-1]]
        if lines[-1] == "" and ends_with_newline
        else [f"{prefix}{lines[-1]}"]
    )

    # Join the lines back together, appropriately handling the final newline
    modified_stdout = "\n".join(modified_lines)
    # if ends_with_newline:
    #     modified_stdout += "\n"

    return modified_stdout


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
    cwd: typing.Optional[pathlib.Path] = None,
) -> None:
    """Logs out useful debug information on '--verbose'."""
    if verbose:
        log(f"running: start: {label}: {cmd_string}")
        if valid_exit_ids is not None:
            valid_exit_strs = ",".join(str(exit_code) for exit_code in valid_exit_ids)
            log(f"\tallowed return ids are: {valid_exit_strs}")

        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            log(f"ENV OVERRIDES: {env_overrides_as_string} {cmd_string}")

        if cwd:
            log(f"cwd: {str(cwd)}")


def run_command(  # noqa: C901
    cmd: typing.List[str],  # 'cmd' is the only thing that can't be optionally kwargs
    label: str,
    verbose: bool,
    env_overrides: typing.Optional[typing.Dict[str, str]] = None,
    ignore_fails: bool = False,
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]] = None,
    cwd: typing.Optional[pathlib.Path] = None,
    record_sub_job_time: typing.Optional[RecordSubJobTimeType] = None,
    **kwargs: typing.Any,
) -> str:
    """Runs the given command, returning stdout or throwing on any error."""
    cmd_string = " ".join(cmd)

    if record_sub_job_time is not None:
        # start the capture of how long this sub-task takes.
        start = timer()

    run_env: typing.Dict[str, str] = _prepare_environment(
        env_overrides,
    )
    _log_command_execution(
        cmd_string,
        label,
        env_overrides,
        valid_exit_ids,
        verbose,
        cwd,
    )

    if valid_exit_ids is None:
        valid_exit_ids = (0,)

    # init the process in case it throws for things like not being able to
    # convert the command to a list of strings.
    process: typing.Optional[Popen[str]] = None
    stdout: str = ""
    try:
        with Popen(
            cmd,
            env=run_env,
            stdout=SUBPROCESS_PIPE,
            stderr=SUBPROCESS_STDOUT,
            cwd=cwd,
            text=True,
            bufsize=1,  # buffer it for every character return
            universal_newlines=True,
        ) as process:
            # Read output line by line as it becomes available
            assert process.stdout is not None
            for line in process.stdout:
                stdout += line
                if verbose:
                    # print each line of output, assuming that each has a newline
                    log(parse_stdout(line, prefix=f"{label}: "))

            # Wait for the subprocess to finish and get the exit code
            process.wait()

            if process.returncode not in valid_exit_ids:
                valid_exit_strs = ",".join(
                    [str(exit_code) for exit_code in valid_exit_ids]
                )
                raise RunCommandBadExitCode(
                    (
                        f"non-zero exit {process.returncode} (allowed are "
                        f"{valid_exit_strs}) from {cmd_string}"
                    )
                )
    except BaseException as err:
        if ignore_fails:
            return ""
        parsed_stdout: str = (
            parse_stdout(stdout, prefix=f"{label}: ERROR: ") if process else ""
        )
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
            f"\n{str(parsed_stdout)}"
            f"\nERROR END"
        )

        if isinstance(err, RunCommandBadExitCode):
            raise RunCommandBadExitCode(error_string) from err
        # fallback to raising a RunCommandUnhandledError
        raise RunCommandUnhandledError(error_string) from err

    if verbose:
        log(f"running: done: {label}: {cmd_string}")

    if record_sub_job_time is not None:
        # Capture how long this run took
        end = timer()
        time_taken: timedelta = timedelta(seconds=end - start)
        record_sub_job_time(label, time_taken)

    return stdout
