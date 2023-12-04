import typing
from collections import defaultdict

from runem.config_metadata import ConfigMetadata
from runem.types import (
    JobConfig,
    JobNames,
    JobPhases,
    JobTags,
    PhaseGroupedJobs,
    PhaseName,
)
from runem.utils import printable_set


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
) -> PhaseGroupedJobs:
    """Filters the jobs to match requested tags."""
    jobs_to_run: JobNames = config_metadata.jobs_to_run
    phases_to_run: JobPhases = config_metadata.phases_to_run
    tags_to_run: JobTags = config_metadata.tags_to_run
    tags_to_avoid: JobTags = config_metadata.tags_to_avoid
    jobs: PhaseGroupedJobs = config_metadata.jobs
    verbose: bool = config_metadata.args.verbose
    if tags_to_run:
        print(f"filtering for tags {printable_set(tags_to_run)}", end="")
    if tags_to_avoid:
        print(f"excluding jobs with tags {printable_set(tags_to_avoid)}", end="")
    if tags_to_run or tags_to_avoid:
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
