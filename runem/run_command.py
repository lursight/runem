import os
import pathlib
import typing
from datetime import timedelta
from subprocess import PIPE as SUBPROCESS_PIPE
from subprocess import STDOUT as SUBPROCESS_STDOUT
from subprocess import Popen
from timeit import default_timer as timer

from rich.markup import escape

from runem.log import log

TERMINAL_WIDTH = 86


class RunemJobError(RuntimeError):
    """An exception type that stores the stdout/stderr.

    Designed so that we do not print the full stdout via the exception stack, instead,
    allows an opportunity to parse the markup in it.
    """

    def __init__(self, friendly_message: str, stdout: str):
        self.stdout = stdout
        super().__init__(friendly_message)


class RunCommandBadExitCode(RunemJobError):
    def __init__(self, stdout: str):
        super().__init__(friendly_message="Bad exit-code", stdout=stdout)


class RunCommandUnhandledError(RunemJobError):
    def __init__(self, stdout: str):
        super().__init__(friendly_message="Unhandled job error", stdout=stdout)


# A function type for recording timing information.
RecordSubJobTimeType = typing.Callable[[str, timedelta], None]


def parse_stdout(stdout: str, prefix: str) -> str:
    """Prefixes each line of output with a given label, except trailing new lines."""
    # Edge case: Return the prefix immediately for an empty string
    if not stdout:
        return prefix

    # Stop errors in `rich` by parsing out anything that might look like
    # rich-markup.
    stdout = escape(stdout)

    # Split stdout into lines
    lines = stdout.split("\n")

    # Apply prefix to all lines except the last if it's empty (due to a trailing newline)
    modified_lines = [f"{prefix}{escape(line)}" for line in lines[:-1]] + (
        [f"{prefix}{escape(lines[-1])}"]
    )

    # Join the lines back together, appropriately handling the final newline
    modified_stdout: str = "\n".join(modified_lines)

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
    decorate_logs: bool,
    verbose: bool,
    cwd: typing.Optional[pathlib.Path] = None,
) -> None:
    """Logs out useful debug information on '--verbose'."""
    if verbose:
        log(
            f"running: start: [blue]{label}[/blue]: [yellow]{cmd_string}[yellow]",
            prefix=decorate_logs,
        )
        if valid_exit_ids is not None:
            valid_exit_strs = ",".join(str(exit_code) for exit_code in valid_exit_ids)
            log(
                f"\tallowed return ids are: [green]{valid_exit_strs}[/green]",
                prefix=decorate_logs,
            )

        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            log(
                f"ENV OVERRIDES: [yellow]{env_overrides_as_string} {cmd_string}[/yellow]",
                prefix=decorate_logs,
            )

        if cwd:
            log(f"cwd: {str(cwd)}", prefix=decorate_logs)


def run_command(  # noqa: C901
    cmd: typing.List[str],  # 'cmd' is the only thing that can't be optionally kwargs
    label: str,
    verbose: bool,
    env_overrides: typing.Optional[typing.Dict[str, str]] = None,
    ignore_fails: bool = False,
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]] = None,
    cwd: typing.Optional[pathlib.Path] = None,
    record_sub_job_time: typing.Optional[RecordSubJobTimeType] = None,
    decorate_logs: bool = True,
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
        decorate_logs,
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
                    log(
                        parse_stdout(
                            line, prefix=f"[green]| [/green][blue]{label}[/blue]: "
                        ),
                        prefix=False,
                    )

            # Wait for the subprocess to finish and get the exit code
            process.wait()

            if process.returncode not in valid_exit_ids:
                valid_exit_strs = ",".join(
                    [str(exit_code) for exit_code in valid_exit_ids]
                )
                raise RunCommandBadExitCode(
                    (
                        f"non-zero exit [red]{process.returncode}[/red] (allowed are "
                        f"[green]{valid_exit_strs}[/green]) from {cmd_string}"
                    )
                )
    except BaseException as err:
        if ignore_fails:
            return ""
        parsed_stdout: str = (
            parse_stdout(stdout, prefix="[red]| [/red]") if process else ""
        )
        env_overrides_as_string = ""
        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            env_overrides_as_string = f"{env_overrides_as_string} "
        error_string = (
            f"runem: [red bold]FATAL[/red bold]: command failed: [blue]{label}[/blue]"
            f"\n\t[yellow]{env_overrides_as_string}{cmd_string}[/yellow]"
            f"\n[red underline]| ERROR[/red underline]: [blue]{label}[/blue]"
            f"\n{str(parsed_stdout)}"
            f"\n[red underline]| ERROR END[/red underline]"
        )

        if isinstance(err, RunCommandBadExitCode):
            raise RunCommandBadExitCode(error_string) from err
        # fallback to raising a RunCommandUnhandledError
        raise RunCommandUnhandledError(error_string) from err

    if verbose:
        log(
            f"running: done: [blue]{label}[/blue]: [yellow]{cmd_string}[/yellow]",
            prefix=decorate_logs,
        )

    if record_sub_job_time is not None:
        # Capture how long this run took
        end = timer()
        time_taken: timedelta = timedelta(seconds=end - start)
        record_sub_job_time(label, time_taken)

    return stdout
