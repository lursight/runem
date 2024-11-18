import pathlib

from runem.job_runner_simple_command import (
    job_runner_simple_command,
    validate_simple_command,
)
from runem.job_wrapper_python import get_job_wrapper_py_func
from runem.types.runem_config import JobWrapper
from runem.types.types_jobs import JobFunction


def get_job_wrapper(job_wrapper: JobWrapper, cfg_filepath: pathlib.Path) -> JobFunction:
    """Given a job-description determines the job-runner, returning it as a function.

    NOTE: Side-effects: also re-addressed the job-config in the case of functions see
          get_job_function.
    """
    if "command" in job_wrapper:
        # validate that the command is "understandable" and usable.
        command_string: str = job_wrapper["command"]
        validate_simple_command(command_string)
        return job_runner_simple_command

    # if we do not have a simple command address assume we have just an addressed
    # function
    return get_job_wrapper_py_func(job_wrapper, cfg_filepath)
