import pathlib
import typing

from runem.types.common import JobName, JobTags, OrderedPhases, PhaseName
from runem.types.filters import TagFileFilter
from runem.types.hooks import HookName


class OptionConfig(typing.TypedDict, total=False):
    """Spec for configuring job option overrides."""

    name: str
    aliases: typing.Optional[typing.List[str]]
    alias: typing.Optional[str]
    default: bool
    type: str
    desc: typing.Optional[str]


OptionConfigs = typing.Tuple[OptionConfig, ...]


class OptionConfigSerialised(typing.TypedDict):
    """Supports better serialisation of options."""

    option: OptionConfig


class JobParamConfig(typing.TypedDict):
    """Configures what parameters are passed to the test-callable.

    FIXME: this isn't actually used at all, yet
    """

    limitFilesToGroup: bool  # whether to limit file-set for the job


class JobAddressConfig(typing.TypedDict):
    """Configuration which described a callable to call."""

    file: str  # the file-module where 'function' can be found
    function: str  # the 'function' in module to run


class JobContextConfig(typing.TypedDict, total=False):
    # what parameters the job needs # DEFUNCT
    params: typing.Optional[JobParamConfig]

    # the path or paths to run the command in. If given a list the job will be
    # duplicated for each given path.
    cwd: typing.Optional[typing.Union[str, typing.List[str]]]


class JobWhen(typing.TypedDict, total=False):
    """Configures WHEN to call the callable i.e. priority."""

    tags: JobTags  # the job tags - used for filtering job-types
    phase: PhaseName  # the phase when the job should be run


class JobWrapper(typing.TypedDict, total=False):
    """A base-type for jobs, hooks, and things that can be invoked."""

    addr: JobAddressConfig  # which callable to call
    command: str  # a one-liner command to be run


class JobConfig(JobWrapper, total=False):
    """A dict that defines a job to be run.

    It consists of the label, address, context and filter information

    TODO: make a class variant of this
    """

    label: JobName  # the name of the job
    ctx: typing.Optional[JobContextConfig]  # how to call the callable
    when: JobWhen  # when to call the job


Jobs = typing.List[JobConfig]


class TagFileFilterSerialised(typing.TypedDict):
    """Supports better serialisation of TagFileFilters."""

    filter: TagFileFilter


class GlobalConfig(typing.TypedDict):
    """The config for the entire test run."""

    # Phases control the order of jobs, jobs earlier in the stack get run earlier
    # the core ide here is to ensure that certain types of job-dependencies,
    # such as code-reformatting jobs run before analysis tools, therefore making
    # any error messages about the code give consistent line numbers e..g if a
    # re-formatter edits a file the error line will move and the analysis phase
    # will report the wrong line.
    phases: OrderedPhases

    # Options control the extra flags that are optionally consumed by job.
    # Options configured here are used to set command-line-options. All options
    # and their current state are passed to each job.
    options: typing.Optional[typing.List[OptionConfigSerialised]]

    # File filters control which files will be passed to jobs for a given tags.
    # Job will receive the super-set of files for all that job's tags.
    files: typing.Optional[typing.List[TagFileFilterSerialised]]

    # Which minimal version of runem does this config support?
    min_version: typing.Optional[str]


class GlobalSerialisedConfig(typing.TypedDict):
    """Intended to make reading a config file easier.

    Unlike JobSerialisedConfig, this type may not actually help readability.

    An intermediary type for serialisation of the global config, the 'global' resides
    inside a 'global' key and therefore is easier to find and reason about.
    """

    config: GlobalConfig


class HookConfig(JobWrapper, total=False):
    """Specification for hooks.

    Like JobConfig with use addr or command to specify what to execute.
    """

    hook_name: HookName  # the hook for when this is called


class HookSerialisedConfig(typing.TypedDict):
    """Intended to make reading a config file easier.

    Also, unlike JobSerialisedConfig, this type may not actually help readability.
    """

    hook: HookConfig


class JobSerialisedConfig(typing.TypedDict):
    """Makes serialised configs easier to read.

    An intermediary typ for serialisation as each 'job' resides inside a 'job' key.

    This makes formatting of YAML config _significantly_ easier to understand.
    """

    job: JobConfig


ConfigNodes = typing.Union[
    GlobalSerialisedConfig, JobSerialisedConfig, HookSerialisedConfig
]
# The config format as it is serialised to/from disk
Config = typing.List[ConfigNodes]
UserConfigMetadata = typing.List[typing.Tuple[Config, pathlib.Path]]
Hooks = typing.DefaultDict[HookName, typing.List[HookConfig]]
# A dictionary to hold hooks, with hook names as keys
HooksStore = typing.Dict[HookName, typing.List[HookConfig]]
PhaseGroupedJobs = typing.DefaultDict[PhaseName, Jobs]
