# pragma: no cover
from typing_extensions import Unpack

from runem.job.job_args import JobArgs
from runem.job.job_function import job_function


@job_function
def _job_task_example(**kwargs: Unpack[JobArgs]) -> None:
    """An example job-task function."""
