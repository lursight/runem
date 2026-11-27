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
import contextlib
import multiprocessing
import os
import pathlib
import sys
import time
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from multiprocessing.managers import DictProxy, ValueProxy
from timeit import default_timer as timer

from rich.spinner import Spinner
from rich.status import Status
from rich.text import Text

from runem.config.config import (
    find_project_cfg,
    load_project_config,
    load_user_configs,
)
from runem.config.config_metadata import ConfigMetadata
from runem.config.config_parse import load_config_metadata
from runem.execute.job_execute import job_execute
from runem.filter.files import find_files
from runem.filter.filter_jobs import filter_jobs
from runem.job.job import Job
from runem.job.job_return import JobReturn
from runem.log import error, log, warn
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.time_entry import TimeEntry
from runem.report.metrics.timing_info import TimeInfo
from runem.report.report_on_run import report_on_run
from runem.report.runem_metrics import (
    JobRunMetadata,
    JobRunMetadatasByPhase,
)
from runem.run_command import RunemJobError
from runem.types.common import JobTags, OrderedPhases, PhaseName
from runem.types.errors import SystemExitBad
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import Config, Jobs, PhaseGroupedJobs
from runem.ux.blocking_print import RICH_CONSOLE
from runem.ux.cli.command_line import RunemArgsParse
from runem.ux.printable_set import printable_set, printable_set_coloured


def _update_progress(
    phase: str,
    running_jobs: typing.Dict[str, str],
    completed_jobs: typing.Dict[str, str],
    all_jobs: Jobs,
    is_running: ValueProxy[bool],
    num_workers: int,
    show_spinner: bool,
) -> None:
    """Updates progress report periodically for running tasks.

    Args:
        phase (str): The currently running phase.
        running_jobs (Dict[str, str]): The currently running jobs.
        completed_jobs (Dict[str, str]): The jobs that have finished work.
        all_jobs (Jobs): All jobs, encompassing both completed and running jobs.
        is_running (ValueProxy[bool]): Flag indicating if jobs are still running.
        num_workers (int): Indicates the number of workers performing the jobs.
        show_spinner (bool): Whether to show the animated spinner or not.
    """
    last_running_jobs_set: typing.Set[str] = set()

    # Using the `rich` module to show a loading spinner on console
    spinner_ctx: typing.Union[Status, typing.ContextManager[None]] = (
        RICH_CONSOLE.status(Spinner("dots", text="Starting tasks..."))
        if show_spinner
        else contextlib.nullcontext()
    )

    with spinner_ctx:
        while is_running.value:
            running_jobs_set: typing.Set[str] = set(running_jobs.values())

            # Progress report
            progress: str = f"{len(completed_jobs)}/{len(all_jobs)}"
            running_jobs_list = printable_set_coloured(
                running_jobs_set,
                "blue",
            )  # Reflect current running jobs accurately
            report: str = (
                f"[green]{phase}[/green]: {progress}({num_workers}): "
                f"{running_jobs_list}"
            )
            if show_spinner:
                assert isinstance(spinner_ctx, Status)
                spinner_ctx.update(Text.from_markup(report))
            else:
                if last_running_jobs_set != running_jobs_set:
                    RICH_CONSOLE.log(report)
                    last_running_jobs_set = running_jobs_set

            # Sleep for reduced CPU usage
            time.sleep(0.1)


def _process_jobs(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
    phase: PhaseName,
    jobs: Jobs,
    show_spinner: bool,
) -> typing.Optional[RunemJobError]:
    """Execute each given job asynchronously.

    This is where the major real-world time savings happen, and it could be
    better, much, much better.

    TODO: this is where we do the scheduling, if we wanted to be smarter about
          it and, for instance, run the longest-running job first with quicker
          jobs completing around it, then we would work out that schedule here.

    returns the exception if the any of sub-procs fails, None otherwise
    """
    max_num_concurrent_procs: int = (
        config_metadata.args.procs
        if config_metadata.args.procs != -1
        else multiprocessing.cpu_count()
    )
    num_concurrent_procs: int = min(max_num_concurrent_procs, len(jobs))
    log(
        (
            f"Running '[green]{phase}[/green]' with {num_concurrent_procs} workers (of "
            f"{max_num_concurrent_procs} max) processing {len(jobs)} jobs"
        )
    )

    subprocess_error: typing.Optional[RunemJobError] = None

    with multiprocessing.Manager() as manager:
        running_jobs: DictProxy[typing.Any, typing.Any] = manager.dict()
        completed_jobs: DictProxy[typing.Any, typing.Any] = manager.dict()
        is_running: ValueProxy[bool] = manager.Value("b", True)

        terminal_writer_process = multiprocessing.Process(
            target=_update_progress,
            args=(
                phase,
                running_jobs,
                completed_jobs,
                jobs,
                is_running,
                num_concurrent_procs,
                show_spinner,
            ),
        )
        terminal_writer_process.start()

        try:
            with multiprocessing.Pool(processes=num_concurrent_procs) as pool:
                # use starmap so we can pass down the job-configs and the args and the files
                in_out_job_run_metadatas[phase].extend(
                    pool.starmap(
                        job_execute,  # no kwargs passed for jobs here
                        zip(
                            jobs,
                            repeat(running_jobs),
                            repeat(completed_jobs),
                            repeat(config_metadata),
                            repeat(file_lists),
                            repeat(None),  # <- metadata
                        ),
                    )
                )
        except RunemJobError as err:  # pylint: disable=broad-exception-caught
            subprocess_error = err
        finally:
            # Signal the terminal_writer process to exit
            is_running.value = False
            terminal_writer_process.join()

    return subprocess_error


def _process_jobs_by_phase(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    filtered_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
    show_spinner: bool,
) -> typing.Optional[RunemJobError]:
    """Execute each job asynchronously, grouped by phase.

    Whilst it is conceptually useful to group jobs by 'phase', Phases are
    ostensibly a poor-man's dependency graph. With a proper dependency graph
    Phases could be phased out, or at least used less. For new users, and to get
    a quick and dirty solution up and running, Phases are probably a very good
    idea and easy to grasp.

    TODO: augment (NOT REPLACE) with dependency graph. New users and hacker
          dev-ops/SREs find phases useful and, more importantly, quick to
          implement.

    returns the exception, if any thrown during run.
    """
    for phase in config_metadata.phases:
        jobs = filtered_jobs_by_phase[phase]
        if not jobs:
            # As previously reported, no jobs for this phase
            continue

        if config_metadata.args.verbose:
            log(f"Running Phase {phase}")

        failure_exception: typing.Optional[RunemJobError] = _process_jobs(
            config_metadata,
            file_lists,
            in_out_job_run_metadatas,
            phase,
            jobs,
            show_spinner,
        )
        if failure_exception is not None:
            if config_metadata.args.verbose:
                error(f"running phase {phase}: aborting run")
            return failure_exception

    # ALl phases completed aok.
    return None


MainReturnType = typing.Tuple[
    ConfigMetadata, JobRunMetadatasByPhase, typing.Optional[RunemJobError]
]


def _load_config_for_run(argv: typing.List[str]) -> ConfigMetadata:
    """High level run-prep orchestration

    This function orchestrates:
        - project loading
        - user-config loading
        - populating args with config-specs
        - filtering the run-read config/graph
        - returns filtered run-ready config.

    This is where the power of run'em resides. We match a declarative config with useful
    command-line switches to make choosing which jobs to run fast and intuitive.

    Args:
        argv: command line argv

    Returns:
            ConfigMetadata object with all the required information.
    """
    cfg_filepath: pathlib.Path = find_project_cfg()
    # Args-parsing and config are tightly coupled.
    args_parse = RunemArgsParse(cfg_filepath)

    # Early-parse argv for built-ins and controls we will apply during
    # config-parsing
    args_parse.parse_early(argv)
    assert args_parse.args is not None
    args: argparse.Namespace = args_parse.args

    if args.verbose:
        log(f"loaded config from {cfg_filepath}")

    # Load the config
    config: Config = load_project_config()
    user_configs: typing.List[typing.Tuple[Config, pathlib.Path]] = load_user_configs()
    config_metadata: ConfigMetadata = load_config_metadata(
        config,
        cfg_filepath,
        user_configs,
        args,
    )
    args_parse.parse_with_config(argv, config_metadata)
    config_metadata.set_cli_data(args_parse.args)
    return config_metadata


def _format_filter_tags(
    tags: JobTags,
    file_filter_tags: JobTags,
) -> str:
    """Separate requested tags that have file filters from those that do not."""
    with_filters: typing.Set[str] = tags.intersection(file_filter_tags)
    without_filters: typing.Set[str] = tags.difference(file_filter_tags)
    return (
        f"with filters [{printable_set(with_filters) or 'none'}], "
        f"without filters [{printable_set(without_filters) or 'none'}]"
    )


def _get_file_filter_tags_for_jobs(
    filtered_jobs: PhaseGroupedJobs,
    configured_file_filter_tags: JobTags,
) -> JobTags:
    """Return file-filter tags needed by jobs that survived CLI filtering."""
    implied_tags: JobTags = set()
    for phase_jobs in filtered_jobs.values():
        for job in phase_jobs:
            job_tags: typing.Optional[JobTags] = Job.get_job_tags(job)
            if job_tags is None:
                # Untagged jobs consume every file batch, so their presence makes
                # every configured file filter relevant to this run.
                return configured_file_filter_tags
            implied_tags.update(job_tags.intersection(configured_file_filter_tags))
    return implied_tags


def _log_filter_context(
    config_metadata: ConfigMetadata,
    filtered_jobs: PhaseGroupedJobs,
) -> None:
    """Explain the file and tag filters that contribute to this run."""
    args: argparse.Namespace = config_metadata.args
    file_filter_tags: JobTags = set(config_metadata.file_filters)

    if args.jobs_given_on_cli:
        required_file_filter_tags: JobTags = _get_file_filter_tags_for_jobs(
            filtered_jobs,
            file_filter_tags,
        )
        log(
            "file filters implied by selected --jobs: "
            f"{_format_filter_tags(required_file_filter_tags, file_filter_tags)}"
        )


def _log_file_selection_modes(args: argparse.Namespace) -> None:
    """Log which file-selection switches will constrain discovery."""
    active_file_modes: typing.List[str] = []
    if args.check_modified_files:
        active_file_modes.append("-f")
    if args.check_head_files:
        active_file_modes.append("-h")
    if args.git_since_branch is not None:
        active_file_modes.append(f"--git-files-since-branch={args.git_since_branch}")
    if not active_file_modes:
        active_file_modes.append("all tracked files")
    log(f"file selection modes: {', '.join(active_file_modes)}")


def _partition_jobs_by_file_availability(
    filtered_jobs: PhaseGroupedJobs,
    file_lists: FilePathListLookup,
) -> typing.Tuple[PhaseGroupedJobs, PhaseGroupedJobs]:
    """Remove jobs with no matching files before creating execution workers."""
    jobs_with_files: PhaseGroupedJobs = defaultdict(list)
    jobs_without_files: PhaseGroupedJobs = defaultdict(list)
    for phase, phase_jobs in filtered_jobs.items():
        for job in phase_jobs:
            job_tags = Job.get_job_tags(job)
            if Job.has_files(file_lists, job_tags):
                jobs_with_files[phase].append(job)
            else:
                jobs_without_files[phase].append(job)
    return jobs_with_files, jobs_without_files


def _log_jobs_without_files(
    jobs_without_files: PhaseGroupedJobs,
    silent: bool,
) -> None:
    """Report all jobs that preflight removed from execution in one warning."""
    if silent:
        return
    job_names: typing.Set[str] = set()
    for phase_jobs in jobs_without_files.values():
        for job in phase_jobs:
            job_names.add(Job.get_job_name(job))
    if job_names:
        warn(f"skipping jobs with no files: {printable_set(job_names)}")


def _record_jobs_without_files(
    jobs_without_files: PhaseGroupedJobs,
    job_run_metadatas: JobRunMetadatasByPhase,
) -> None:
    """Keep zero-duration skip records without dispatching jobs to workers."""
    for phase, phase_jobs in jobs_without_files.items():
        for job in phase_jobs:
            label = Job.get_job_name(job)
            no_files_timing = JobTiming(
                job=TimeEntry(
                    label=f"{label}: no files!",
                    info=TimeInfo(start=0, end=0),
                ),
                commands=[],
            )
            job_run_metadatas[phase].append((no_files_timing, None))


def _main(
    argv: typing.List[str],
) -> MainReturnType:
    start = timer()

    config_metadata: ConfigMetadata = _load_config_for_run(argv)

    # first anchor the cwd to the config-file, so that git ls-files works
    os.chdir(config_metadata.cfg_filepath.parent)

    if config_metadata.args.verbose:
        _log_file_selection_modes(config_metadata.args)

    filtered_jobs_by_phase: PhaseGroupedJobs = filter_jobs(
        config_metadata=config_metadata,
    )
    if config_metadata.args.verbose:
        _log_filter_context(config_metadata, filtered_jobs_by_phase)

    configured_file_filter_tags: JobTags = set(config_metadata.file_filters)
    required_file_filter_tags: JobTags = _get_file_filter_tags_for_jobs(
        filtered_jobs_by_phase,
        configured_file_filter_tags,
    )
    has_jobs_to_check: bool = any(filtered_jobs_by_phase.values())
    if has_jobs_to_check and required_file_filter_tags:
        file_lists: FilePathListLookup = find_files(
            config_metadata,
            file_filter_tags=required_file_filter_tags,
        )
    else:
        # With no selected jobs or matching file filters, discovery cannot help a job.
        file_lists = defaultdict(list)

    if config_metadata.args.verbose:
        log(f"found {len(file_lists)} batches, ", end="")
        for tag in sorted(file_lists.keys()):
            file_list = file_lists[tag]
            log(f"{len(file_list)} '{tag}' files, ", prefix=False, end="")
        log(prefix=False)

    (
        filtered_jobs_by_phase,
        jobs_without_files,
    ) = _partition_jobs_by_file_availability(
        filtered_jobs_by_phase,
        file_lists,
    )
    _log_jobs_without_files(jobs_without_files, config_metadata.args.silent)
    end = timer()

    job_run_metadatas: JobRunMetadatasByPhase = defaultdict(list)
    pre_build_time = JobTiming(
        job=TimeEntry(
            label="pre-build",
            info=TimeInfo(start=start, end=end),
        ),
        commands=[],
    )
    job_run_metadatas["_app"].append((pre_build_time, None))
    _record_jobs_without_files(jobs_without_files, job_run_metadatas)

    start = timer()

    failure_exception: typing.Optional[RunemJobError] = _process_jobs_by_phase(
        config_metadata,
        file_lists,
        filtered_jobs_by_phase,
        job_run_metadatas,
        show_spinner=config_metadata.args.show_spinner,
    )

    end = timer()

    phase_run_timing = JobTiming(
        job=TimeEntry(
            label="run-phases",
            info=TimeInfo(start=start, end=end),
        ),
        commands=[],
    )
    phase_run_report: JobReturn = None
    phase_run_metadata: JobRunMetadata = (phase_run_timing, phase_run_report)
    job_run_metadatas["_app"].append(phase_run_metadata)
    return config_metadata, job_run_metadatas, failure_exception


def timed_main(argv: typing.List[str]) -> None:
    """A main-entry point that runs the application reports on it.

    IMPORTANT: this should remain a lightweight wrapper around _main() so that timings
               are representative.
    """
    start = timer()
    config_metadata: ConfigMetadata
    job_run_metadatas: JobRunMetadatasByPhase
    failure_exception: typing.Optional[RunemJobError]
    config_metadata, job_run_metadatas, failure_exception = _main(argv)
    phase_run_oder: OrderedPhases = config_metadata.phases
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    wall_clock_time_saved: timedelta
    system_time_spent: timedelta
    system_time_spent, wall_clock_time_saved = report_on_run(
        phase_run_oder, job_run_metadatas, time_taken
    )
    message: str = "[green bold]DONE[/green bold]: runem took"
    if failure_exception:
        message = "[red bold]FAILED[/red bold]: your jobs failed after"
    log(
        (
            f"{message}: {time_taken.total_seconds()}s, "
            f"saving you [green]{wall_clock_time_saved.total_seconds()}s[/green], "
            "without runem you would have waited "
            f"[red]{system_time_spent.total_seconds()}s[/red]"
        )
    )

    config_metadata.hook_manager.invoke_on_exit(
        metadata={
            "run_success": failure_exception is None,
            "wall_clock_time_saved_s": wall_clock_time_saved.total_seconds(),
        }
    )

    if failure_exception is not None:
        # we got a failure somewhere, now that we've reported the timings we
        # re-raise.
        error(failure_exception.stdout)
        raise SystemExitBad(1) from failure_exception


if __name__ == "__main__":
    timed_main(sys.argv)
