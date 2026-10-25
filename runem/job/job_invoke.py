import typing
from datetime import timedelta

from typing_extensions import NotRequired

from runem.types.common import FilePathList


class JobInvokeArgs(typing.TypedDict, total=True):
    """Defines the task-specific args for job-task functions.

    This concrete type defines the arguments that must be passed into Job
    execution invocations.
    """

    file_list: FilePathList
    record_sub_job_time: NotRequired[
        typing.Optional[typing.Callable[[str, timedelta], None]]
    ]
