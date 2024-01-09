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
import multiprocessing
import os
import pathlib
import sys
import time
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from multiprocessing.managers import DictProxy, ListProxy, ValueProxy
from timeit import default_timer as timer

from halo import Halo

from runem.command_line import parse_args
from runem.config import load_config
from runem.config_metadata import ConfigMetadata
from runem.config_parse import parse_config
from runem.files import find_files
from runem.job_execute import job_execute
from runem.job_filter import filter_jobs
from runem.log import log
from runem.report import report_on_run
from runem.types import (
    Config,
    FilePathListLookup,
    JobReturn,
    JobRunMetadata,
    JobRunMetadatasByPhase,
    Jobs,
    JobTiming,
    OrderedPhases,
    PhaseGroupedJobs,
    PhaseName,
)
from runem.utils import printable_set


def _determine_run_parameters(argv: typing.List[str]) -> ConfigMetadata:
    """Loads config, parsing cli input and produces the run config.

    This is where the power of run'em resides. We match a declarative config with useful
    command-line switches to make choosing which jobs to run fast and intuitive.

    Return a ConfigMetadata object with all the required information.
    """
    config: Config
    cfg_filepath: pathlib.Path
    config, cfg_filepath = load_config()
    config_metadata: ConfigMetadata = parse_config(config, cfg_filepath)

    # Now we parse the cli arguments extending them with information from the
    # .runem.yml config.
    config_metadata = parse_args(config_metadata, argv)

    if config_metadata.args.verbose:
        log(f"loaded config from {cfg_filepath}")

    return config_metadata


def _update_progress(
    label: str,
    running_jobs: typing.Dict[str, str],
    seen_jobs: typing.List[str],
    all_jobs: Jobs,
    is_running: ValueProxy[bool],
    num_workers: int,
) -> None:
    """Updates progress report periodically for running tasks.

    Args:
        label (str): The identifier.
        running_jobs (Dict[str, str]): The currently running jobs.
        seen_jobs (List[str]): Jobs that the function has previously tracked.
        all_jobs (Jobs): All jobs, encompassing both completed and running jobs.
        is_running (ValueProxy[bool]): Flag indicating if jobs are still running.
        num_workers (int): Indicates the number of workers performing the jobs.
    """
    # Using Halo library to show a loading spinner on console
    spinner = Halo(text="", spinner="dots")
    spinner.start()

    # The set of all job labels, and the set of completed jobs
    all_job_names: typing.Set[str] = {job["label"] for job in all_jobs}
    completed_jobs: typing.Set[str] = set()

    # This dataset is used to track changes between iterations
    last_running_jobs_set: typing.Set[str] = set()

    while is_running.value:
        running_jobs_set: typing.Set[str] = set(running_jobs.values())
        seen_jobs = list(running_jobs_set.union(seen_jobs))  # Update the seen jobs

        # Jobs that have disappeared since last check
        disappeared_jobs: typing.Set[str] = last_running_jobs_set - running_jobs_set

        # Jobs that have not yet completed
        remaining_jobs: typing.Set[str] = all_job_names - completed_jobs

        # Check if we're closing to completion
        workers_retiring: bool = len(remaining_jobs) <= num_workers

        if workers_retiring:
            # Handle edge case: a task may have disappeared whilst process was sleeping
            all_completed_jobs: typing.Set[str] = all_job_names - remaining_jobs
            disappeared_jobs.update(all_completed_jobs - running_jobs_set)

        completed_jobs.update(disappeared_jobs)

        # Prepare progress report
        progress: str = f"{len(completed_jobs)}/{len(all_jobs)}"
        running_jobs_list = printable_set(running_jobs_set)
        spinner.text = f"{label}: {progress}({num_workers}): {running_jobs_list}"

        # Update the tracked dataset for the next iteration
        last_running_jobs_set = running_jobs_set

        # Sleep to decrease frequency of updates and reduce CPU usage
        time.sleep(0.1)

    spinner.stop()


def _process_jobs(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
    phase: PhaseName,
    jobs: Jobs,
) -> None:
    """Execute each given job asynchronously.

    This is where the major real-world time savings happen, and it could be
    better, much, much better.

    TODO: this is where we do the scheduling, if we wanted to be smarter about
          it and, for instance, run the longest-running job first with quicker
          jobs completing around it, then we would work out that schedule here.
    """
    max_num_concurrent_procs: int = (
        config_metadata.args.procs
        if config_metadata.args.procs != -1
        else multiprocessing.cpu_count()
    )
    num_concurrent_procs: int = min(max_num_concurrent_procs, len(jobs))
    log(
        (
            f"Running '{phase}' with {num_concurrent_procs} workers (of "
            f"{max_num_concurrent_procs} max) processing {len(jobs)} jobs"
        )
    )

    with multiprocessing.Manager() as manager:
        seen_jobs: ListProxy[str] = manager.list()
        running_jobs: DictProxy[typing.Any, typing.Any] = manager.dict()
        is_running: ValueProxy[bool] = manager.Value("b", True)

        terminal_writer_process = multiprocessing.Process(
            target=_update_progress,
            args=(
                phase,
                running_jobs,
                seen_jobs,
                jobs,
                is_running,
                num_concurrent_procs,
            ),
        )
        terminal_writer_process.start()

        try:
            with multiprocessing.Pool(processes=num_concurrent_procs) as pool:
                # use starmap so we can pass down the job-configs and the args and the files
                in_out_job_run_metadatas[phase] = pool.starmap(
                    job_execute,
                    zip(
                        jobs,
                        repeat(running_jobs),
                        repeat(config_metadata),
                        repeat(file_lists),
                    ),
                )
        finally:
            # Signal the terminal_writer process to exit
            is_running.value = False
            terminal_writer_process.join()


def _process_jobs_by_phase(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    filtered_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
) -> None:
    """Execute each job asynchronously, grouped by phase.

    Whilst it is conceptually useful to group jobs by 'phase', Phases are
    ostensibly a poor-man's dependency graph. With a proper dependency graph
    Phases could be phased out, or at least used less. For new users, and to get
    a quick and dirty solution up and running, Phases are probably a very good
    idea and easy to grasp.

    TODO: augment (NOT REPLACE) with dependency graph. New users and hacker
          dev-ops/SREs find phases useful and, more importantly, quick to
          implement.
    """
    for phase in config_metadata.phases:
        jobs = filtered_jobs_by_phase[phase]
        if not jobs:
            # As previously reported, no jobs for this phase
            continue

        if config_metadata.args.verbose:
            log(f"Running Phase {phase}")

        _process_jobs(
            config_metadata, file_lists, in_out_job_run_metadatas, phase, jobs
        )


def _main(
    argv: typing.List[str],
) -> typing.Tuple[OrderedPhases, JobRunMetadatasByPhase]:
    start = timer()

    config_metadata: ConfigMetadata = _determine_run_parameters(argv)

    # first anchor the cwd to the config-file, so that git ls-files works
    os.chdir(config_metadata.cfg_filepath.parent)

    file_lists: FilePathListLookup = find_files(config_metadata)
    assert file_lists
    log(f"found {len(file_lists)} batches, ", end="")
    for tag in sorted(file_lists.keys()):
        file_list = file_lists[tag]
        log(f"{len(file_list)} '{tag}' files, ", decorate=False, end="")
    log(decorate=False)  # new line

    filtered_jobs_by_phase: PhaseGroupedJobs = filter_jobs(
        config_metadata=config_metadata,
    )
    end = timer()

    job_run_metadatas: JobRunMetadatasByPhase = defaultdict(list)
    job_run_metadatas["_app"].append(
        (("pre-build", (timedelta(seconds=end - start))), None)
    )

    start = timer()

    _process_jobs_by_phase(
        config_metadata, file_lists, filtered_jobs_by_phase, job_run_metadatas
    )

    end = timer()

    phase_run_timing: JobTiming = ("run-phases", timedelta(seconds=end - start))
    phase_run_report: JobReturn = None
    phase_run_metadata: JobRunMetadata = (phase_run_timing, phase_run_report)
    job_run_metadatas["_app"].append(phase_run_metadata)
    return config_metadata.phases, job_run_metadatas


def timed_main(argv: typing.List[str]) -> None:
    """A main-entry point that runs the application reports on it.

    IMPORTANT: this should remain a lightweight wrapper around _main() so that timings
               are representative.
    """
    start = timer()
    phase_run_oder: OrderedPhases
    job_run_metadatas: JobRunMetadatasByPhase
    phase_run_oder, job_run_metadatas = _main(argv)
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    time_saved = report_on_run(phase_run_oder, job_run_metadatas, time_taken)
    log(
        (
            f"DONE: runem took: {time_taken.total_seconds()}s, "
            f"saving you {time_saved.total_seconds()}s"
        )
    )


if __name__ == "__main__":
    timed_main(sys.argv)
