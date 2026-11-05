from runem.job.job_args import JobArgs
from runem.job.job_example import _job_task_example

# pylint: disable=protected-access


def test_job_task_example() -> None:
    kwargs: JobArgs = {"a": "a"}  # type:ignore
    _job_task_example(**kwargs)
