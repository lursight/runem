"""

Some note on Unpack and kwargs:
    We *try* to strongly type `**kwargs` for clarity.
    We have tried several ways to define a Generic type that encapsulates
        `**kwargs: SingleType`
    ... but none of the solutions worked with python 3.9 -> 3.12 and mypy 1.9.0,
    so we have to recommend instead using:
        `**kwargs: Unpack[KwArgsType]`

    For this to work across versions of python where support for Unpack changes;
    for example `Unpack` is a python 3.12 feature, but available in the
    `typing_extensions` module.

    So, for now, it looks like we get away with importing `Unpack` from the
    `typing_extensions` module, even in python 3.12, so we will use, and
    recommend using, the `typing_extensions` of `Unpack`, until it becomes
    obsolete.

    Alternatively, we can use the following, but it's unnecessarily verbose.

    if sys.version_info >= (3, 12):  # pragma: no coverage
        from typing import Unpack
    else:  # pragma: no coverage
        from typing_extensions import Unpack
"""

import pathlib
import typing
from datetime import timedelta

from typing_extensions import Unpack

from runem.types.common import FilePathList, PhaseName
from runem.types.options import Options
from runem.types.runem_config import JobConfig

if typing.TYPE_CHECKING:  # pragma: no cover
    from runem.config_metadata import ConfigMetadata

ReportName = str
ReportUrl = typing.Union[str, pathlib.Path]
ReportUrlInfo = typing.Tuple[ReportName, ReportUrl]
ReportUrls = typing.List[ReportUrlInfo]


class JobReturnData(typing.TypedDict, total=False):
    """A dict that defines job result to be reported to the user."""

    reportUrls: ReportUrls  # urls containing reports for the user


TimingEntry = typing.Tuple[str, timedelta]
TimingEntries = typing.List[TimingEntry]


class JobTiming(typing.TypedDict, total=True):
    """A hierarchy of timing info. Job->JobCommands.

    The overall time for a job is in 'job', the child calls to run_command are in
    'commands'
    """

    job: TimingEntry  # the overall time for a job
    commands: TimingEntries  # timing for each call to `run_command`


JobReturn = typing.Optional[JobReturnData]
JobRunMetadata = typing.Tuple[JobTiming, JobReturn]
JobRunTimesByPhase = typing.Dict[PhaseName, typing.List[JobTiming]]
JobRunReportByPhase = typing.Dict[PhaseName, ReportUrls]
JobRunMetadatasByPhase = typing.Dict[PhaseName, typing.List[JobRunMetadata]]


class CommonKwargs(
    typing.TypedDict,
    total=True,  # each of these are guaranteed to exist in jobs and hooks
):
    """Defines the base args that are passed to all jobs.

    As we call hooks and job-task in the same manner, this defines the variables that we
    can access from both hooks and job-tasks.
    """

    config_metadata: "ConfigMetadata"  # gives greater context to jobs and hooks
    job: JobConfig  # the job or hook task spec ¢ TODO: rename this
    label: str  # the name of the hook or the job-label
    options: Options  # options passed in on the command line
    procs: int  # the max number of concurrent procs to run
    root_path: pathlib.Path  # the path where the .runem.yml file is
    verbose: bool  # control log verbosity


class HookSpecificKwargs(typing.TypedDict, total=False):
    """Defines the args that are passed down to the hooks.

    NOTE: that although these however
     outside of the *hook* context, the data will not be present. Such is the
     difficulty in dynamic programming.
    """

    wall_clock_time_saved: timedelta  # only on `HookName.ON_EXIT`


class JobTaskKwargs(
    typing.TypedDict,
    total=False,  # for now, we don't enforce these types for job-context, but we should.
):
    """Defines the task-specific args for job-task functions."""

    file_list: FilePathList
    record_sub_job_time: typing.Optional[typing.Callable[[str, timedelta], None]]


class HookKwargs(CommonKwargs, HookSpecificKwargs):
    """A merged set of kwargs for runem-hooks."""

    pass


class JobKwargs(CommonKwargs, JobTaskKwargs):
    """A merged set of kwargs for job-tasks."""

    pass


class AllKwargs(CommonKwargs, JobTaskKwargs, HookSpecificKwargs):
    """A merged set of kwargs for al job-functions."""

    pass


@typing.runtime_checkable
class JobFunction(typing.Protocol):
    def __call__(self, **kwargs: Unpack[AllKwargs]) -> JobReturn:  # pragma: no cover
        """Defines the call() protocol's abstract pattern for job-tasks."""

    @property
    def __name__(self) -> str:  # pragma: no cover
        """Defines the name protocol for job-task functions.

        This is primarily used for internal tests but can be useful for introspection.
        """


def _hook_example(
    wall_clock_time_saved: timedelta,
    **kwargs: typing.Any,
) -> None:
    """An example hook."""


def _job_task_example(
    **kwargs: Unpack[JobKwargs],
) -> None:
    """An example job-task function."""
