import typing
from collections import defaultdict

from runem.config_metadata import ConfigMetadata
from runem.job import Job
from runem.log import log
from runem.types.common import JobNames, JobPhases, JobTags, PhaseName
from runem.types.runem_config import JobConfig, PhaseGroupedJobs
from runem.utils import printable_set


def _should_filter_out_by_tags(
    job: JobConfig,
    tags: JobTags,
    tags_to_avoid: JobTags,
    verbose: bool,
) -> bool:
    job_tags: typing.Optional[JobTags] = Job.get_job_tags(job)
    opted_into_tag_filtering: bool = job_tags is not None
    if not opted_into_tag_filtering:
        # TODO: should we also consider 'empty' tags and being opted out of
        #       tag-filtering?
        return False

    # the config for the command has tags, use them
    assert job_tags is not None  # for mypy
    matching_tags = job_tags.intersection(tags)
    if not matching_tags:
        if verbose:
            log(
                (
                    f"not running job '{Job.get_job_name(job)}' because it doesn't have "
                    f"any of the following tags: {printable_set(tags)}"
                )
            )
        return True  # filter-out this job

    has_tags_to_avoid = job_tags.intersection(tags_to_avoid)
    if has_tags_to_avoid:
        if verbose:
            log(
                (
                    f"not running job '{Job.get_job_name(job)}' because it contains the "
                    f"following tags: {printable_set(has_tags_to_avoid)}"
                )
            )
        return True  # filter-out this job

    # no filter criteria met, filter-in the job i.e. run the job
    return False


def _get_jobs_matching(
    phase: PhaseName,
    job_names: JobNames,
    tags: JobTags,
    tags_to_avoid: JobTags,
    jobs: PhaseGroupedJobs,
    filtered_jobs: PhaseGroupedJobs,
    verbose: bool,
) -> None:
    """Via filtered_jobs, filters 'jobs' that match the given phase and and tags.

    Warns if the job-name isn't found in list of valid job-names.
    """
    phase_jobs: typing.List[JobConfig] = jobs[phase]

    job: JobConfig
    for job in phase_jobs:
        if _should_filter_out_by_tags(job, tags, tags_to_avoid, verbose):
            continue

        job_name: str = Job.get_job_name(job)
        if job_name not in job_names:
            # test test_get_jobs_matching_when_job_not_in_valid_job_names should
            # cover the follow in Ci but does not for some reason I don't have
            # time to look in to. /FH
            if verbose:  # pragma: FIXME: add code coverage
                log(
                    (
                        f"not running job '{job_name}' because it isn't in the "
                        f"list of job names. See --jobs and --not-jobs"
                    )
                )
            continue

        filtered_jobs[phase].append(job)


def filter_jobs(  # noqa: C901
    config_metadata: ConfigMetadata,
) -> PhaseGroupedJobs:
    """Filters the jobs to match requested tags."""
    jobs_to_run: JobNames = config_metadata.jobs_to_run
    phases_to_run: JobPhases = config_metadata.phases_to_run
    tags_to_run: JobTags = config_metadata.tags_to_run
    tags_to_avoid: JobTags = config_metadata.tags_to_avoid
    jobs: PhaseGroupedJobs = config_metadata.jobs
    verbose: bool = config_metadata.args.verbose
    if verbose:
        if tags_to_run:
            log(
                f"filtering for tags {printable_set(tags_to_run)}",
                decorate=True,
                end="",
            )
        if tags_to_avoid:
            if tags_to_run:
                log(", ", decorate=False, end="")
            else:
                log(decorate=True, end="")
            log(
                f"excluding jobs with tags {printable_set(tags_to_avoid)}",
                decorate=False,
                end="",
            )
        if tags_to_run or tags_to_avoid:
            log(decorate=False)
    filtered_jobs: PhaseGroupedJobs = defaultdict(list)
    for phase in config_metadata.phases:
        if phase not in phases_to_run:
            # test test_get_jobs_matching_when_job_not_in_valid_job_names should
            # cover the follow in Ci but does not for some reason I don't have
            # time to look in to. /FH
            if verbose:  # pragma: FIXME: add code coverage
                log(f"skipping phase '{phase}'")
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
            # test test_get_jobs_matching_when_job_not_in_valid_job_names should
            # cover the follow in Ci but does not for some reason I don't have
            # time to look in to. /FH
            if verbose:  # pragma: FIXME: add code coverage
                log(f"No jobs for phase '{phase}' tags {printable_set(tags_to_run)}")
            continue

        if verbose:
            log((f"will run {len(filtered_jobs[phase])} jobs for phase '{phase}'"))
            job_names: JobNames = {
                Job.get_job_name(job) for job in filtered_jobs[phase]
            }
            log(f"\t{printable_set(job_names)}")

    return filtered_jobs
