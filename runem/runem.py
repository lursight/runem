#!/usr/bin/env python3
"""`runem`, runs Lursight's dev-ops tools, hopefully as fast as possible.

We don't yet:
- account for load
- check for diffs in code to only test changed code
- do any git-related stuff, like:
  - compare head to merge-target branch
  - check for changed files
- support non-git repos
- not stream stdout to terminal
- have inter-job dependencies as that requires a smarter scheduler, we use woraround
  this with phases, for now

We do:
- use git ls-files
- run as many jobs as possible
- hope that resources are enough i.e. we DO NOT measure resource use, yet.
- time tests and tell you what used the most time, and how much time run-tests saved
  you
"""
import argparse
import importlib
import importlib.util
import inspect
import multiprocessing
import os
import pathlib
import re
import subprocess
import sys
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from timeit import default_timer as timer

try:
    import termplotlib
except ImportError:
    termplotlib = None

import yaml

CFG_FILE_YMAL = pathlib.Path(".runem.yml")


class FunctionNotFound(ValueError):
    """Thrown when the test-function cannot be found."""

    pass


JobName = str
JobTag = str
PhaseName = str

TimingDataPhase = typing.Dict[PhaseName, typing.List[typing.Tuple[str, timedelta]]]


class OptionConfig(typing.TypedDict):
    """Speci for configuring job option overrides."""

    name: str
    aliases: typing.Optional[typing.List[str]]
    default: bool
    type: str
    desc: typing.Optional[str]


OptionName = str
OptionValue = bool

OptionConfigs = typing.Tuple[OptionConfig, ...]
Options = typing.Dict[OptionName, OptionValue]

# P1: bool for verbose, P2: list of file paths to work on


class TagFileFilter(typing.TypedDict):
    tag: str
    regex: str


TagFileFilters = typing.Dict[JobTag, TagFileFilter]
FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
FilePathListLookup = typing.DefaultDict[JobTag, FilePathList]


# FIXME: this type is no-longer the actual spec of the test-functions
JobFunction = typing.Callable[[argparse.Namespace, Options, FilePathList], None]


class JobParamConfig(typing.TypedDict):
    """Configures what paramters are passed to the test-callable.

    FIXME: this isn't actually used at all, yet
    """

    limitFilesToGroup: bool  # whether to limit file-set for the job


class JobAddressConfig(typing.TypedDict):
    """Configuration which described a callable to call."""

    file: str  # the file-module where 'function' can be found
    function: str  # the 'function' in module to run


class JobContextConfig(typing.TypedDict):
    params: JobParamConfig  # what parameters the job needs
    cwd: typing.Optional[str]  # the path to run the command in


class JobWhen(typing.TypedDict):
    """Configures WHEN to call the callable i.e. priority."""

    tags: typing.List[str]  # the job tags - used for filtering job-types
    phase: str  # the phase when the job should be run


class JobConfig(typing.TypedDict):
    """A dict that defines a job to be run.

    It consists of the label, adress, context and filter information
    """

    label: str  # the name of the job
    addr: JobAddressConfig  # which callable to call
    ctx: JobContextConfig  # how to call the callable
    when: JobWhen  # when to call the job


Jobs = typing.List[JobConfig]

# meta-data types
JobNames = typing.Set[JobName]
JobPhases = typing.Set[str]
JobTags = typing.Set[JobTag]
OrderedPhases = typing.Tuple[PhaseName, ...]
PhaseGroupedJobs = typing.DefaultDict[PhaseName, typing.List[JobConfig]]


class ConfigMetadata:
    phases: OrderedPhases  # the phases and orders to run them in
    options: OptionConfigs  # the options to add to the cli and pass to jobs
    file_filters: TagFileFilters  # which files to get for which tag
    jobs: PhaseGroupedJobs  # the jobs to be run ordered by phase
    job_names: JobNames  # the set of job-names
    job_phases: JobPhases  # the set of job-phases (should be subset of 'phases')
    job_tags: JobTags  # the set of job-tags (used for filtering)

    def __init__(
        self,
        cfg_filepath: pathlib.Path,
        phases: OrderedPhases,
        options: OptionConfigs,
        file_filters: TagFileFilters,
        jobs: PhaseGroupedJobs,
        job_names: JobNames,
        job_phases: JobPhases,
        job_tags: JobTags,
    ) -> None:
        self.cfg_filepath = cfg_filepath
        self.phases = phases
        self.options = options
        self.file_filters = file_filters
        self.jobs = jobs
        self.job_names = job_names
        self.job_phases = job_phases
        self.job_tags = job_tags


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
    # reformatter edits a file the error line will move and the analysis phase
    # will report the wrong line.
    phases: OrderedPhases

    # Options control the extra flags that are optionaly consumed by job.
    # Options configured here are used to set command-line-options. All options
    # and their current state are passed to each job.
    options: typing.List[OptionConfigSerialised]

    # File filters control which files will be passed to jobs for a given tags.
    # Job will recieve the super-set of files for all that job's tags.
    files: typing.List[TagFileFilterSerialised]


class GlobalSerialisedConfig(typing.TypedDict):
    """Intended to make reading a config file easier.

    Unlike JobSerialisedConfig, this type may not actually help readabilty.

    An intermediary type for serialisation of the global config, the 'global' resides
    inside a 'global' key and therefore is easier to find and reason about.
    """

    config: GlobalConfig


class JobSerialisedConfig(typing.TypedDict):
    """Makes serialised configs easier to read.

    An intermediary typ for serialisation as each 'job' resides inside a 'job' key.

    This makes formatting of YAML configd _significantly_ easier to understand.
    """

    job: JobConfig


ConfigNodes = typing.Union[GlobalSerialisedConfig, JobSerialisedConfig]
# The config format as it is serialised to/from disk
Config = typing.List[ConfigNodes]


def _parse_args(
    config_metadata: ConfigMetadata, argv: typing.List[str]
) -> typing.Tuple[argparse.Namespace, JobNames, JobPhases, JobTags, JobTags, Options]:
    """Parses the args and defines the filter inputs.

    Generates args based upon the config, parsing the cli args and return the filters to
    be used when selecting jobs.

    Returns the parsed args, the jobs_names_to_run, job_phases_to_run, job_tags_to_run
    """
    parser = argparse.ArgumentParser(description="Runs the Lursight Lang test-suite")

    job_group = parser.add_argument_group("jobs")
    all_job_names: JobNames = set(name for name in config_metadata.job_names)
    job_group.add_argument(
        "--jobs",
        dest="jobs",
        nargs="+",
        default=sorted(list(all_job_names)),
        help=(
            "List of job-names to run the given jobs. Other filters will modify this list. "
            f"Defaults to '{sorted(list(all_job_names))}'"
        ),
        required=False,
    )
    job_group.add_argument(
        "--not-jobs",
        dest="jobs_excluded",
        nargs="+",
        default=[],
        help=(
            "List of job-names to NOT run. Defaults to empty. "
            f"Available options are: '{sorted(list(all_job_names))}'"
        ),
        required=False,
    )

    phase_group = parser.add_argument_group("phases")
    phase_group.add_argument(
        "--phases",
        dest="phases",
        nargs="+",
        default=config_metadata.job_phases,
        help=(
            "Run only the phases passed in, and can be used to "
            "change the phase order. Phases are run in the order given. "
            f"Defaults to '{config_metadata.job_phases}'. "
        ),
        required=False,
    )
    phase_group.add_argument(
        "--not-phases",
        dest="phases_excluded",
        nargs="+",
        default=[],
        help=(
            "List of phases to NOT run. "
            "This option does not change the phase run order. "
            f"Options are '{sorted(config_metadata.job_phases)}'. "
        ),
        required=False,
    )

    tag_group = parser.add_argument_group("tags")
    tag_group.add_argument(
        "--tags",
        dest="tags",
        nargs="+",
        default=config_metadata.job_tags,
        help=(
            "Only jobs with the given tags. "
            f"Defaults to '{sorted(config_metadata.job_tags)}'."
        ),
        required=False,
    )
    tag_group.add_argument(
        "--not-tags",
        dest="tags_excluded",
        nargs="+",
        default=[],
        help=(
            "Removes one or more tags from the list of job tags to be run. "
            f"Options are '{sorted(config_metadata.job_tags)}'."
        ),
        required=False,
    )

    job_param_overrides_group = parser.add_argument_group(
        "job-param overrides",  # help="overrides default test params on all matching jobs"
    )
    _define_option_args(config_metadata, job_param_overrides_group)

    parser.add_argument(
        "--call-graphs",
        dest="generate_call_graphs",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    parser.add_argument(
        "--procs",
        "-j",
        # "-n",
        dest="procs",
        default=-1,
        help=(
            "the number of concurrent test jobs to run, -1 runs all test jobs at the same time "
            f"({os.cpu_count()} cores available)"
        ),
        required=False,
        type=int,
    )

    config_dir: pathlib.Path = config_metadata.cfg_filepath.parent
    parser.add_argument(
        "--root",
        dest="root_dir",
        default=config_dir,
        help=(
            "which dir to use as the base-dir for testing, "
            f"defaults to directory containing the config '{config_dir}'"
        ),
        required=False,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    args = parser.parse_args(argv[1:])

    options: Options = _initialise_options(config_metadata, args)

    if not _validate_filters(config_metadata, args):
        sys.exit(1)

    # apply the cli filters to produce the high-level requirements. These will be used
    # to further filter the jobs.
    jobs_to_run = set(args.jobs).difference(args.jobs_excluded)
    tags_to_run = set(args.tags).difference(args.tags_excluded)
    tags_to_avoid = set(args.tags_excluded)
    phases_to_run = set(args.phases).difference(args.phases_excluded)

    return args, jobs_to_run, phases_to_run, tags_to_run, tags_to_avoid, options


def _validate_filters(
    config_metadata: ConfigMetadata,
    args: argparse.Namespace,
) -> bool:
    """Validates the command line filters given.

    returns True of success and False on failure
    """
    # validate the job-names passed in
    for name, name_list in (("only", args.jobs), ("exclude", args.jobs_excluded)):
        for job_name in name_list:
            if job_name not in config_metadata.job_names:
                print(
                    (
                        f"ERROR: invalid {name}-job-name '{job_name}', "
                        f"choose from one of {config_metadata.job_names}"
                    )
                )
                return False

    # validate the tags passed in
    for name, tag_list in (("only", args.tags), ("exclude", args.tags_excluded)):
        for tag in tag_list:
            if tag not in config_metadata.job_tags:
                print(
                    (
                        f"ERROR: invalid {name}-tag '{tag}', "
                        f"choose from one of {config_metadata.job_tags}"
                    )
                )
                return False

    # validate the phases passed in
    for name, phase_list in (("only", args.phases), ("exclude", args.phases_excluded)):
        for phase in phase_list:
            if phase not in config_metadata.job_phases:
                print(
                    (
                        f"ERROR: invalid {name}-phase '{phase}', "
                        f"choose from one of {config_metadata.job_phases}"
                    )
                )
                return False
    return True


def _initialise_options(
    config_metadata: ConfigMetadata,
    args: argparse.Namespace,
) -> Options:
    """Initialises and returns the set of options to use for this run.

    Returns the options dictionary
    """

    options: Options = {
        option["name"]: option["default"] for option in config_metadata.options
    }
    if config_metadata.options and args.overrides_on:
        for option_name in args.overrides_on:
            options[option_name] = True
    if config_metadata.options and args.overrides_off:
        for option_name in args.overrides_off:
            options[option_name] = False
    return options


def _define_option_args(
    config_metadata: ConfigMetadata, job_param_overrides_group: argparse._ArgumentGroup
) -> None:
    option: OptionConfig
    for option in config_metadata.options:
        switch_name = option["name"].replace("_", "-").replace(" ", "-")

        aliases: typing.List[str] = []
        aliases_no: typing.List[str] = []
        if "aliases" in option and option["aliases"]:
            aliases = [
                _alias_to_switch(switch_name_alias)
                for switch_name_alias in option["aliases"]
            ]
            aliases_no = [
                _alias_to_switch(switch_name_alias, negatise=True)
                for switch_name_alias in option["aliases"]
            ]

        desc: typing.Optional[str] = None
        desc_for_off: typing.Optional[str] = None
        if "desc" in option:
            desc = option["desc"]
            desc_for_off = f"turn off {desc}"

        job_param_overrides_group.add_argument(
            f"--{switch_name}",
            *aliases,
            dest="overrides_on",
            action="append_const",
            const=option["name"],
            help=desc,
            required=False,
        )
        job_param_overrides_group.add_argument(
            f"--no-{switch_name}",
            *aliases_no,
            dest="overrides_off",
            action="append_const",
            const=option["name"],
            help=desc_for_off,
            required=False,
        )


def _alias_to_switch(switch_name_alias: str, negatise: bool = False) -> str:
    """Util function to generate a alias switch for argsparse."""
    if not negatise and len(switch_name_alias) == 1:
        return f"-{switch_name_alias}"
    if negatise:
        return f"--no-{switch_name_alias}"
    return f"--{switch_name_alias}"


def _search_up_dirs_for_file(
    start_dir: pathlib.Path, search_filename: typing.Union[str, pathlib.Path]
) -> typing.Optional[pathlib.Path]:
    """Search 'up' from start_dir looking for search_filename."""
    while 1:
        cfg_cand = start_dir / search_filename
        if cfg_cand.exists():
            return cfg_cand
        exhausted_stack: bool = start_dir == start_dir.parent
        if exhausted_stack:
            return None
        start_dir = start_dir.parent


def _search_up_multiple_dirs_for_file(
    start_dirs: typing.Iterable[pathlib.Path],
    search_filename: typing.Union[str, pathlib.Path],
) -> typing.Optional[pathlib.Path]:
    """Same as _search_up_dirs_for_file() but for multiple dir start points."""
    for start_dir in start_dirs:
        found: typing.Optional[pathlib.Path] = _search_up_dirs_for_file(
            start_dir, search_filename
        )
        if found is not None:
            return found
    return None


def _find_cfg() -> pathlib.Path:
    """Searches up from the cwd for a .runem.yml config file."""
    start_dirs = (pathlib.Path(".").absolute(),)
    cfg_cand: typing.Optional[pathlib.Path] = _search_up_multiple_dirs_for_file(
        start_dirs, CFG_FILE_YMAL
    )
    if cfg_cand:
        return cfg_cand

    # error out and exit as we currently require the cfg file as it lists jobs.
    print(f"ERROR: Config not found! Looked from {start_dirs}")
    sys.exit(1)


def _load_config() -> typing.Tuple[Config, pathlib.Path]:
    """Finds and loads the .runem.yml file."""
    cfg_filepath: pathlib.Path = _find_cfg()
    with cfg_filepath.open("r+", encoding="utf-8") as config_file_handle:
        all_config = yaml.full_load(config_file_handle)
    return all_config, cfg_filepath


def _find_files(config_metadata: ConfigMetadata) -> FilePathListLookup:
    file_lists: FilePathListLookup = defaultdict(list)

    file_paths: typing.List[str] = (
        subprocess.check_output(
            "git ls-files",
            shell=True,
        )
        .decode("utf-8")
        .splitlines()
    )
    _bucket_file_by_tag(
        file_paths,
        config_metadata,
        in_out_file_lists=file_lists,
    )

    # now ensure the file lists are sorted so we get deterministic behavior in tests
    for job_type in file_lists:
        file_lists[job_type] = sorted(file_lists[job_type])
    return file_lists


def _bucket_file_by_tag(  # noqa: C901 # pylint: disable=too-many-branches
    file_paths: typing.List[str],
    config_metadata: ConfigMetadata,
    in_out_file_lists: FilePathListLookup,
) -> None:
    """Groups files by the file.filters iin the config."""
    for file_path in file_paths:
        for tag, file_filter in config_metadata.file_filters.items():
            if re.search(file_filter["regex"], file_path):
                in_out_file_lists[tag].append(file_path)


def _run_job(
    job_config: JobConfig,
    cfg_filepath: pathlib.Path,
    args: argparse.Namespace,
    file_lists: FilePathListLookup,
    options: Options,
) -> typing.Tuple[str, timedelta]:
    label = job_config["label"]
    if args.verbose:
        print(f"START: {label}")
    root_path: pathlib.Path = cfg_filepath.parent
    function: typing.Callable
    job_tags: JobTags = set(job_config["when"]["tags"])
    os.chdir(root_path)
    function = get_test_function(job_config, cfg_filepath)

    # get the files for all files found for this job's tags
    file_list: FilePathList = []
    for tag in job_tags:
        if tag in file_lists:
            file_list.extend(file_lists[tag])

    if not file_list:
        # no files to work on
        print(f"WARNING: skipping job '{label}', no files for job")
        return (f"{label}: no files!", timedelta(0))
    if job_config["ctx"]["cwd"]:
        os.chdir(root_path / job_config["ctx"]["cwd"])
    else:
        os.chdir(root_path)

    start = timer()
    func_signature = inspect.signature(function)
    if args.verbose:
        print(f"sub-proc: running {job_config['label']}")
    if "args" in func_signature.parameters:
        function(args, options, file_list)
    else:
        function(
            options=options,  # type: ignore
            file_list=file_list,  # type: ignore
            procs=args.procs,
            root_path=root_path,
            verbose=args.verbose,
            **job_config,
        )
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    if args.verbose:
        print(f"DONE: {label}: {time_taken}")
    return (label, time_taken)


def _get_test_function(
    cfg_filepath: pathlib.Path,
    module_name: str,
    module_file_path: pathlib.Path,
    function_to_load: str,
) -> JobFunction:
    """Given a job-description dynamically loads the test-function so we can call it."""
    # load the function
    module_spec = importlib.util.spec_from_file_location(
        function_to_load, module_file_path
    )
    if not module_spec:
        raise FunctionNotFound(
            f"unable to load '${function_to_load}' from '{module_file_path}"
        )

    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    if not module_spec.loader:
        raise FunctionNotFound("unable to load module")
    module_spec.loader.exec_module(module)
    try:
        function: JobFunction = getattr(module, function_to_load)
    except AttributeError as err:
        raise FunctionNotFound(
            (
                f"ERROR! Check that function '{function_to_load}' "
                f"exists in '{module_file_path}' as expected in "
                f"your config at '{str(cfg_filepath)}"
            )
        ) from err
    return function


def _find_job_module(cfg_filepath: pathlib.Path, module_file_path: str) -> pathlib.Path:
    """Attempts to find the true location of the job-function module."""
    module_path: pathlib.Path = pathlib.Path(module_file_path)

    module_path_cands = [
        module_path.absolute(),
        (cfg_filepath.parent / module_file_path).absolute(),
    ]
    for module_path in module_path_cands:
        if module_path.exists():
            break
    if not module_path.exists():
        raise FunctionNotFound(
            (
                f"unable to find test-function module looked in {module_path_cands} running "
                f"from '{pathlib.Path('.').absolute()}'"
            )
        )
    module_path = module_path.absolute()
    return module_path.relative_to(pathlib.Path(".").absolute())


def get_test_function(job_config: JobConfig, cfg_filepath: pathlib.Path) -> JobFunction:
    """Given a job-description dynamically loads the test-function so we can call it.

    Also re-address the job-config.
    """
    function_to_load: str = job_config["addr"]["function"]
    try:
        module_file_path: pathlib.Path = _find_job_module(
            cfg_filepath, job_config["addr"]["file"]
        )
    except FunctionNotFound as err:
        raise FunctionNotFound(
            (
                f"Whilst loading job '{job_config['label']}' runem failed to find "
                f"job.addr.file '{job_config['addr']['file']}' looking for "
                f"job.addr.function '{function_to_load}'"
            )
        ) from err

    module_name = module_file_path.stem.replace(" ", "_").replace("-", "_")

    try:
        function = _get_test_function(
            cfg_filepath, module_name, module_file_path, function_to_load
        )
    except FunctionNotFound:
        print(
            (
                f"WARNING: job: '{job_config['label']}': Failed to find "
                f"function file {job_config['addr']['file']}"
            )
        )
        # re-write the file entry in the job
        job_config["addr"]["file"] = __file__
        module_file_path = pathlib.Path(job_config["addr"]["file"])
        # the follow may throw if the fun isn't in this file, as intended
        function = _get_test_function(
            cfg_filepath, module_name, module_file_path, function_to_load
        )

    # re-write the job-config file-path for the module with the one that worked
    job_config["addr"]["file"] = str(module_file_path)
    return function


def _get_jobs_matching(
    phase: PhaseName,
    job_names: JobNames,
    tags: JobTags,
    tags_to_avoid: JobTags,
    jobs: PhaseGroupedJobs,
    filtered_jobs: PhaseGroupedJobs,
    verbose: bool,
) -> None:
    phase_jobs: typing.List[JobConfig] = jobs[phase]

    job: JobConfig
    for job in phase_jobs:
        job_tags = set(job["when"]["tags"])
        matching_tags = job_tags.intersection(tags)
        if not matching_tags:
            if verbose:
                print(
                    (
                        f"not running job '{job['label']}' because it doesn't have "
                        f"any of the following tags: {tags}"
                    )
                )
            continue

        if job["label"] not in job_names:
            if verbose:
                print(
                    (
                        f"not running job '{job['label']}' because it isn't in the "
                        f"list of job names. See --jobs and --not-jobs"
                    )
                )
            continue

        has_tags_to_avoid = job_tags.intersection(tags_to_avoid)
        if has_tags_to_avoid:
            if verbose:
                print(
                    (
                        f"not running job '{job['label']}' because it contains the "
                        f"following tags: {has_tags_to_avoid}"
                    )
                )
            continue

        filtered_jobs[phase].append(job)


def filter_jobs(
    config_metadata: ConfigMetadata,
    jobs_to_run: JobNames,
    phases_to_run: JobPhases,
    tags_to_run: JobTags,
    tags_to_avoid: JobTags,
    jobs: PhaseGroupedJobs,
    verbose: bool,
) -> PhaseGroupedJobs:
    """Filters the jobs to match requested tags."""
    filtered_jobs: PhaseGroupedJobs = defaultdict(list)
    for phase in config_metadata.phases:
        if phase not in phases_to_run:
            print(f"skipping phase '{phase}'")
            continue
        _get_jobs_matching(
            phase=phase,
            job_names=jobs_to_run,
            tags=tags_to_run,
            tags_to_avoid=tags_to_avoid,
            jobs=jobs,
            filtered_jobs=filtered_jobs,
            verbose=verbose,
        )
        if len(filtered_jobs[phase]) == 0:
            print(f"No jobs for phase '{phase}' tags '{tags_to_run}'")
            continue

        print(
            (
                f"will run {len(filtered_jobs[phase])} jobs "
                f"for phase '{phase}' with tags '{tags_to_run}'"
            )
        )
        print(f"\t{[job['label'] for job in filtered_jobs[phase]]}")

    return filtered_jobs


def _parse_global_config(
    global_config: GlobalConfig,
) -> typing.Tuple[OrderedPhases, OptionConfigs, TagFileFilters]:
    """Parses and validates a global-config entry read in from disk.

    Returns the phases in the order we want to run them
    """
    options: OptionConfigs = ()
    if "options" in global_config:
        options = tuple(
            option_serialised["option"]
            for option_serialised in global_config["options"]
        )

    file_filters: TagFileFilters = {}
    if "files" in global_config:
        file_filter: TagFileFilterSerialised
        serialised_filters: typing.List[TagFileFilterSerialised] = global_config[
            "files"
        ]
        for file_filter in serialised_filters:
            actual_filter: TagFileFilter = file_filter["filter"]
            tag = actual_filter["tag"]
            file_filters[tag] = actual_filter

    return global_config["phases"], options, file_filters


def _parse_job_config(
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    in_out_tags: JobTags,
    in_out_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_names: JobNames,
    in_out_phases: JobPhases,
) -> None:
    """Parses and validates a job-entry read in from disk.

    Tries to relocate the function address relative to the config-file

    Returns the tags generated
    """
    try:
        job_names_used = job["label"] in in_out_job_names
        if job_names_used:
            print("ERROR: duplicate job label!")
            print(f"\t'{job['label']}' is used twice or more in {str(cfg_filepath)}")
            sys.exit(1)

        # try and load the function _before_ we schedule it's execution
        get_test_function(job, cfg_filepath)
        phase_id: PhaseName = job["when"]["phase"]
        in_out_jobs_by_phase[phase_id].append(job)

        in_out_job_names.add(job["label"])
        in_out_phases.add(job["when"]["phase"])
        for tag in job["when"]["tags"]:
            in_out_tags.add(tag)
    except KeyError as err:
        raise ValueError(f"job config entry is missing data {job}") from err


def _parse_config(config: Config, cfg_filepath: pathlib.Path) -> ConfigMetadata:
    """Validates and restructure the config to make it more convienient to use."""
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    job_phases: JobPhases = set()
    tags: JobTags = set()
    entry: ConfigNodes
    seen_global: bool = False
    phase_order: OrderedPhases = ()
    options: OptionConfigs = ()
    file_filters: TagFileFilters = {}
    for entry in config:
        # we apply a type-ignore here as we know (for now) that jobs have "job"
        # keys and global configs have "global" keys
        isinstance_job: bool = "job" in entry  # type: ignore
        if not isinstance_job:
            # we apply a type-ignore here as we know (for now) that jobs have "job"
            # keys and global configs have "global" keys
            isinstance_global: bool = "config" in entry  # type: ignore
            if isinstance_global:
                if seen_global:
                    raise ValueError(
                        "Found two global config entries, expected only one 'config' section. "
                        f"second one is {entry}"
                    )
                global_entry: GlobalSerialisedConfig = entry  # type: ignore  # see above
                global_config: GlobalConfig = global_entry["config"]
                phase_order, options, file_filters = _parse_global_config(global_config)
                assert phase_order, "phase order defined in config but is empty!"
                continue

            # not a global or a job entry, what is it
            raise RuntimeError(f"invalid 'job' or 'global' config entry, {entry}")

        job_entry: JobSerialisedConfig = entry  # type: ignore  # see above
        job: JobConfig = job_entry["job"]
        _parse_job_config(
            cfg_filepath,
            job,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=job_phases,
        )

    if not phase_order:
        print("WARNING: phase ordering not configured! Runs will be non-deterministic!")
        phase_order = tuple(job_phases)

    # tags = tags.union(("python", "es", "firebase_funcs"))
    return ConfigMetadata(
        cfg_filepath,
        phase_order,
        options,
        file_filters,
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    )


def _plot_times(
    overall_run_time: timedelta,
    phase_run_oder: OrderedPhases,
    timing_data: TimingDataPhase,
) -> timedelta:
    """Prints a report to terminal on how well we performed."""
    labels: typing.List[str] = []
    times: typing.List[float] = []
    job_time_sum: timedelta = timedelta()  # init to 0
    for phase in phase_run_oder:
        # print(f"Phase '{phase}' jobs took:")
        phase_total_time: float = 0.0
        phase_start_idx = len(labels)
        for label, job_time in timing_data[phase]:
            if job_time.total_seconds() == 0:
                continue
            labels.append(f"│├{phase}.{label}")
            times.append(job_time.total_seconds())
            job_time_sum += job_time
            phase_total_time += job_time.total_seconds()
        labels.insert(phase_start_idx, f"├{phase} (total)")
        times.insert(phase_start_idx, phase_total_time)

    for label, job_time in reversed(timing_data["_app"]):
        labels.insert(0, f"├runem.{label}")
        times.insert(0, job_time.total_seconds())
    labels.insert(0, "runem")
    times.insert(0, overall_run_time.total_seconds())
    if termplotlib:
        fig = termplotlib.figure()
        fig.barh(times, labels, force_ascii=False)
        fig.show()
    else:
        for label, time in zip(labels, times):
            print(f"{label}: {time}s")

    time_saved: timedelta = job_time_sum - overall_run_time
    return time_saved


def _main(  # noqa: C901 # pylint: disable=too-many-branches,too-many-statements
    argv: typing.List[str],
) -> typing.Tuple[OrderedPhases, TimingDataPhase]:
    job_times: TimingDataPhase = defaultdict(list)
    start = timer()
    config: Config
    cfg_filepath: pathlib.Path
    config, cfg_filepath = _load_config()
    config_metadata: ConfigMetadata = _parse_config(config, cfg_filepath)
    args: argparse.Namespace
    tags_to_run: JobTags
    options: Options
    (
        args,
        jobs_to_run,
        phases_to_run,
        tags_to_run,
        tags_to_avoid,
        options,
    ) = _parse_args(config_metadata, argv)

    if args.verbose:
        print(f"loaded config from {cfg_filepath}")

    file_lists: FilePathListLookup = _find_files(config_metadata)
    assert file_lists
    print(f"found {len(file_lists)} batches, ", end="")
    for tag in sorted(file_lists.keys()):
        file_list = file_lists[tag]
        print(f"{len(file_list)} '{tag}' files, ", end="")
    print()  # new line

    filtered_jobs_by_phase: PhaseGroupedJobs = filter_jobs(
        config_metadata=config_metadata,
        jobs_to_run=jobs_to_run,
        phases_to_run=phases_to_run,
        tags_to_run=tags_to_run,
        tags_to_avoid=tags_to_avoid,
        jobs=config_metadata.jobs,
        verbose=args.verbose,
    )
    end = timer()

    job_times["_app"].append(("pre-build", timedelta(seconds=end - start)))

    start = timer()

    for phase in config_metadata.phases:
        jobs = filtered_jobs_by_phase[phase]
        if not jobs:
            # As previously reported, no jobs for this phase
            continue

        if phase not in phases_to_run:
            if args.verbose:
                print(f"Skipping Phase {phase}")
            continue

        if args.verbose:
            print(f"Running Phase {phase}")

        num_concurrent_procs: int = (
            args.procs if args.procs != -1 else multiprocessing.cpu_count()
        )
        num_concurrent_procs = min(num_concurrent_procs, len(jobs))
        print(
            (
                f"Running '{phase}' with {num_concurrent_procs} workers "
                f"processesing {len(jobs)} jobs"
            )
        )
        with multiprocessing.Pool(processes=num_concurrent_procs) as pool:
            # use starmap so we can pass down the job-configs and the args and the files

            job_times[phase] = pool.starmap(
                _run_job,
                zip(
                    jobs,
                    repeat(cfg_filepath),
                    repeat(args),
                    repeat(file_lists),
                    repeat(options),
                ),
            )
    end = timer()

    job_times["_app"].append(("run-phases", timedelta(seconds=end - start)))
    return config_metadata.phases, job_times


def timed_main(argv: typing.List[str]) -> None:
    start = timer()
    phase_run_oder: OrderedPhases
    job_times: TimingDataPhase
    phase_run_oder, job_times = _main(argv)
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    time_saved: timedelta = _plot_times(
        overall_run_time=time_taken,
        phase_run_oder=phase_run_oder,
        timing_data=job_times,
    )
    print(
        (
            f"DONE: runem took: {time_taken.total_seconds()}s, "
            f"saving you {time_saved.total_seconds()}s"
        )
    )


if __name__ == "__main__":
    timed_main(sys.argv)
