import pathlib

from runem.job_wrapper_python import get_job_wrapper_py_func
from runem.types import JobConfig, JobFunction


def get_job_wrapper(job_config: JobConfig, cfg_filepath: pathlib.Path) -> JobFunction:
    """Returns a pythonic job-wrapper function that can be called to run a job."""
    return get_job_wrapper_py_func(job_config, cfg_filepath)
