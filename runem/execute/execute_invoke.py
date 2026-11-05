import pathlib
import typing
from typing import Generic, TypeVar

from typing_extensions import NotRequired

from runem.hook.hook_args import HookArgs

if typing.TYPE_CHECKING:
    from runem.config.config_metadata import ConfigMetadata
    from runem.job.job_options.options import Options
    from runem.types.runem_config import JobConfig

MetadataT = TypeVar("MetadataT", bound=HookArgs.HookData | None)


class CommonKwargs(typing.TypedDict, Generic[MetadataT]):
    """Defines the base args that are passed to all jobs.

    As we call hooks and job-task in the same manner, this defines the variables that we
    can access from both hooks and job-tasks.

    Wide = CommonKwargs[A | B | C]
    Narrow = CommonKwargs[B]
    """

    config_metadata: "ConfigMetadata"  # gives greater context to jobs and hooks
    job: "JobConfig"  # the job or hook task spec ¢ TODO: rename this
    label: str  # the name of the hook or the job-label
    options: "Options"  # options passed in on the command line
    procs: int  # the max number of concurrent procs to run
    root_path: pathlib.Path  # the path where the .runem.yml file is
    verbose: bool  # control log verbosity
    metadata: NotRequired[MetadataT]
