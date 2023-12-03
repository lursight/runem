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
- have inter-job dependencies as that requires a smarter scheduler, we workaround
  this with phases, for now

We do:
- use git ls-files
- run as many jobs as possible
- hope that resources are enough i.e. we DO NOT measure resource use, yet.
- time tests and tell you what used the most time, and how much time run-tests saved
  you
"""
import argparse
import inspect
import multiprocessing
import os
import pathlib
import sys
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from timeit import default_timer as timer

from runem.config import load_config
from runem.config_parse import parse_config
from runem.files import find_files
from runem.job_function_python import get_job_function
from runem.types import (
    Config,
    ConfigMetadata,
    FilePathList,
    FilePathListLookup,
    JobConfig,
    JobNames,
    JobPhases,
    JobReturn,
    JobRunMetadata,
    JobRunMetadatasByPhase,
    JobRunReportByPhase,
    JobRunTimesByPhase,
    JobTags,
    JobTiming,
    OptionConfig,
    Options,
    OrderedPhases,
    PhaseGroupedJobs,
    PhaseName,
)

try:
    import termplotlib
except ImportError:
    termplotlib = None


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


def _run_job(
    job_config: JobConfig,
    cfg_filepath: pathlib.Path,
    args: argparse.Namespace,
    file_lists: FilePathListLookup,
    options: Options,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    label = job_config["label"]
    if args.verbose:
        print(f"START: {label}")
    root_path: pathlib.Path = cfg_filepath.parent
    function: typing.Callable
    job_tags: JobTags = set(job_config["when"]["tags"])
    os.chdir(root_path)
    function = get_job_function(job_config, cfg_filepath)

    # get the files for all files found for this job's tags
    file_list: FilePathList = []
    for tag in job_tags:
        if tag in file_lists:
            file_list.extend(file_lists[tag])

    if not file_list:
        # no files to work on
        print(f"WARNING: skipping job '{label}', no files for job")
        return (f"{label}: no files!", timedelta(0)), None
    if (
        "ctx" in job_config
        and job_config["ctx"] is not None
        and "cwd" in job_config["ctx"]
        and job_config["ctx"]["cwd"]
    ):
        os.chdir(root_path / job_config["ctx"]["cwd"])
    else:
        os.chdir(root_path)

    start = timer()
    func_signature = inspect.signature(function)
    if args.verbose:
        print(f"job: running {job_config['label']}")
    reports: JobReturn
    if "args" in func_signature.parameters:
        reports = function(args, options, file_list)
    else:
        reports = function(
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
    timing_data = (label, time_taken)
    return (timing_data, reports)


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
    print(f"filtering for tags {tags_to_run}", end="")
    if tags_to_avoid:
        print("excluding jobs with tags {tags_to_avoid}", end="")
    print()
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

        print((f"will run {len(filtered_jobs[phase])} jobs for phase '{phase}'"))
        print(f"\t{[job['label'] for job in filtered_jobs[phase]]}")

    return filtered_jobs


def _plot_times(
    overall_run_time: timedelta,
    phase_run_oder: OrderedPhases,
    timing_data: JobRunTimesByPhase,
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
        # cspell:disable-next-line
        fig.barh(
            times,
            labels,
            force_ascii=False,
        )
        fig.show()
    else:
        for label, time in zip(labels, times):
            print(f"{label}: {time}s")

    time_saved: timedelta = job_time_sum - overall_run_time
    return time_saved


def _report_on_run(
    phase_run_oder: OrderedPhases,
    job_run_metadatas: JobRunMetadatasByPhase,
    overall_runtime: timedelta,
):
    timing_data: JobRunTimesByPhase = defaultdict(list)
    report_data: JobRunReportByPhase = defaultdict(list)
    for phase in job_run_metadatas:
        for timing, reports in job_run_metadatas[phase]:
            timing_data[phase].append(timing)
            if reports:
                report_data[phase].extend(reports["reportUrls"])
    time_saved: timedelta = _plot_times(
        overall_run_time=overall_runtime,
        phase_run_oder=phase_run_oder,
        timing_data=timing_data,
    )
    for phase in phase_run_oder:
        for job_report_url_info in report_data[phase]:
            if not job_report_url_info:
                continue
            print(
                f"report: {str(job_report_url_info[0])}: {str(job_report_url_info[1])}"
            )
    return time_saved


def _main(  # noqa: C901 # pylint: disable=too-many-branches,too-many-statements
    argv: typing.List[str],
) -> typing.Tuple[OrderedPhases, JobRunMetadatasByPhase]:
    job_run_metadatas: JobRunMetadatasByPhase = defaultdict(list)
    start = timer()
    config: Config
    cfg_filepath: pathlib.Path
    config, cfg_filepath = load_config()
    config_metadata: ConfigMetadata = parse_config(config, cfg_filepath)
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

    # first anchor the cwd to the config-file, so that git ls-files works
    os.chdir(cfg_filepath.parent)

    file_lists: FilePathListLookup = find_files(config_metadata)
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

    job_run_metadatas["_app"].append(
        (("pre-build", (timedelta(seconds=end - start))), None)
    )

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
                f"processing {len(jobs)} jobs"
            )
        )
        with multiprocessing.Pool(processes=num_concurrent_procs) as pool:
            # use starmap so we can pass down the job-configs and the args and the files

            job_run_metadatas[phase] = pool.starmap(
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

    phase_run_timing: JobTiming = ("run-phases", timedelta(seconds=end - start))
    phase_run_report: JobReturn = None
    phase_run_metadata: JobRunMetadata = (phase_run_timing, phase_run_report)
    job_run_metadatas["_app"].append(phase_run_metadata)
    return config_metadata.phases, job_run_metadatas


def timed_main(argv: typing.List[str]) -> None:
    start = timer()
    phase_run_oder: OrderedPhases
    phase_run_oder, job_run_metadatas = _main(argv)
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    time_saved = _report_on_run(phase_run_oder, job_run_metadatas, time_taken)
    print(
        (
            f"DONE: runem took: {time_taken.total_seconds()}s, "
            f"saving you {time_saved.total_seconds()}s"
        )
    )


if __name__ == "__main__":
    timed_main(sys.argv)
