import argparse
import pathlib
import typing
from datetime import timedelta


class FunctionNotFound(ValueError):
    """Thrown when the test-function cannot be found."""

    pass


# meta-data types
JobName = str
JobTag = str
JobNames = typing.Set[JobName]
JobPhases = typing.Set[str]
JobTags = typing.Set[JobTag]
PhaseName = str
OrderedPhases = typing.Tuple[PhaseName, ...]
ReportName = str
ReportUrl = typing.Union[str, pathlib.Path]
ReportUrlInfo = typing.Tuple[ReportName, ReportUrl]
ReportUrls = typing.List[ReportUrlInfo]


class JobReturnData(typing.TypedDict, total=False):
    """A dict that defines job result to be reported to the user."""

    reportUrls: ReportUrls  # urls containing reports for the user


JobTiming = typing.Tuple[str, timedelta]
JobReturn = typing.Optional[JobReturnData]
JobRunMetadata = typing.Tuple[JobTiming, JobReturn]
JobRunTimesByPhase = typing.Dict[PhaseName, typing.List[JobTiming]]
JobRunReportByPhase = typing.Dict[PhaseName, ReportUrls]
JobRunMetadatasByPhase = typing.Dict[PhaseName, typing.List[JobRunMetadata]]


class OptionConfig(typing.TypedDict, total=False):
    """Spec for configuring job option overrides."""

    name: str
    aliases: typing.Optional[typing.List[str]]
    alias: typing.Optional[str]
    default: bool
    type: str
    desc: typing.Optional[str]


OptionName = str
OptionValue = bool

OptionConfigs = typing.Tuple[OptionConfig, ...]
Options = typing.Dict[OptionName, OptionValue]

# P1: bool for verbose, P2: list of file paths to work on


class TagFileFilter(typing.TypedDict):
    tag: JobTag
    regex: str


TagFileFilters = typing.Dict[JobTag, TagFileFilter]
FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
FilePathListLookup = typing.DefaultDict[JobTag, FilePathList]

# FIXME: this type is no-longer the actual spec of the test-functions
JobFunction = typing.Union[
    typing.Callable[[argparse.Namespace, Options, FilePathList], None],
    typing.Callable[[typing.Any], None],
]


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
    params: typing.Optional[JobParamConfig]  # what parameters the job needs
    cwd: typing.Optional[str]  # the path to run the command in


class JobWhen(typing.TypedDict):
    """Configures WHEN to call the callable i.e. priority."""

    tags: JobTags  # the job tags - used for filtering job-types
    phase: PhaseName  # the phase when the job should be run


class JobConfig(typing.TypedDict, total=False):
    """A dict that defines a job to be run.

    It consists of the label, address, context and filter information
    """

    label: JobName  # the name of the job
    addr: JobAddressConfig  # which callable to call
    ctx: typing.Optional[JobContextConfig]  # how to call the callable
    when: JobWhen  # when to call the job


Jobs = typing.List[JobConfig]

PhaseGroupedJobs = typing.DefaultDict[PhaseName, Jobs]


class OptionConfigSerialised(typing.TypedDict):
    """Supports better serialisation of options."""

    option: OptionConfig


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


class GlobalSerialisedConfig(typing.TypedDict):
    """Intended to make reading a config file easier.

    Unlike JobSerialisedConfig, this type may not actually help readability.

    An intermediary type for serialisation of the global config, the 'global' resides
    inside a 'global' key and therefore is easier to find and reason about.
    """

    config: GlobalConfig


class JobSerialisedConfig(typing.TypedDict):
    """Makes serialised configs easier to read.

    An intermediary typ for serialisation as each 'job' resides inside a 'job' key.

    This makes formatting of YAML config _significantly_ easier to understand.
    """

    job: JobConfig


ConfigNodes = typing.Union[GlobalSerialisedConfig, JobSerialisedConfig]
# The config format as it is serialised to/from disk
Config = typing.List[ConfigNodes]
