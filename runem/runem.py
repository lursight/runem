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
import multiprocessing
import os
import pathlib
import sys
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from timeit import default_timer as timer

from runem.command_line import parse_args
from runem.config import load_config
from runem.config_parse import parse_config
from runem.files import find_files
from runem.job_filter import filter_jobs
from runem.job_runner import job_runner
from runem.report import report_on_run
from runem.types import (
    Config,
    ConfigMetadata,
    FilePathListLookup,
    JobReturn,
    JobRunMetadata,
    JobRunMetadatasByPhase,
    JobTags,
    JobTiming,
    Options,
    OrderedPhases,
    PhaseGroupedJobs,
)


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
    ) = parse_args(config_metadata, argv)

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
                job_runner,
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
    time_saved = report_on_run(phase_run_oder, job_run_metadatas, time_taken)
    print(
        (
            f"DONE: runem took: {time_taken.total_seconds()}s, "
            f"saving you {time_saved.total_seconds()}s"
        )
    )


if __name__ == "__main__":
    timed_main(sys.argv)
