import os
import subprocess
import typing

TERMINAL_WIDTH = 86


def get_stdout(process: subprocess.CompletedProcess, prefix: str) -> str:
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
    env_overrides: typing.Optional[dict] = None,
    ignore_fails: bool = False,
    valid_exit_ids: typing.Optional[typing.Tuple[int, ...]] = None,
    **kwargs: typing.Any,
) -> str:
    """Runs the given command, returning stdout or throwing on any error."""
    cmd_string: str = " ".join(cmd)
    if verbose:
        print(f"runem: running: start: {label}: {cmd_string}")
        if valid_exit_ids is not None:
            valid_exit_strs = ",".join([str(exit_code) for exit_code in valid_exit_ids])
            print(f"allowed return ids are: {valid_exit_strs}")

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
        print(f"RUN ENV OVERRIDES: {run_env_as_string } {cmd_string}")

        if env_overrides:
            env_overrides_as_string = " ".join(
                [f"{key}='{value}'" for key, value in env_overrides.items()]
            )
            print(f"ENV OVERRIDES: {env_overrides_as_string} {cmd_string}")

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
    if run_env:
        run_env_param = run_env

    process: subprocess.CompletedProcess
    try:
        process = subprocess.run(
            cmd,
            check=False,  # Do NOT throw on non-zero exit
            env=run_env_param,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )  # raise on non-zero
        if process.returncode not in valid_exit_ids:
            valid_exit_strs = ",".join([str(exit_code) for exit_code in valid_exit_ids])
            raise RuntimeError(
                (
                    f"non-zero exit {process.returncode} (alowed are "
                    f"{valid_exit_strs}) from {cmd_string}"
                )
            )
    except BaseException as err:
        if ignore_fails:
            return ""
        stdout: str = get_stdout(process, prefix=f"{label}: ERROR: ")
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
        raise RuntimeError(error_string) from err

    cmd_stdout: str = get_stdout(process, prefix=label)
    if verbose:
        print(cmd_stdout)
        print(f"runem: running: done: {label}: {cmd_string}")
    return cmd_stdout
