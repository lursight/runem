import typing

from typing_extensions import Unpack

from runem.job.job_args import JobArgs
from runem.job.job_return import JobReturn


@typing.runtime_checkable
class JobFunction(typing.Protocol):
    def __call__(self, **kwargs: Unpack[JobArgs]) -> JobReturn:  # pragma: no cover
        """Defines the call() protocol's abstract pattern for job-tasks."""

    @property
    def __name__(self) -> str:  # pragma: no cover
        """Defines the name protocol for job-task functions.

        This is primarily used for internal tests but can be useful for introspection.
        """


JobFunctionBind = typing.TypeVar("JobFunctionBind", bound=JobFunction)


def job_function(fn: JobFunctionBind) -> JobFunctionBind:
    return fn
