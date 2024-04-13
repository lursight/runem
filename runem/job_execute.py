import os
import pathlib
import typing
import uuid
from datetime import timedelta
from timeit import default_timer as timer

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import ReadOnlyInformativeDict
from runem.job import Job
from runem.job_wrapper import get_job_wrapper
from runem.log import error, log
from runem.types import (
    FilePathListLookup,
    JobConfig,
    JobFunction,
    JobReturn,
    JobTags,
    JobTiming,
    TimingEntries,
    TimingEntry,
)


def job_execute_inner(
    job_config: JobConfig,
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    **kwargs: typing.Any,
) -> typing.Tuple[JobTiming, JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label = Job.get_job_name(job_config)
    if config_metadata.args.verbose:
        log(f"START: '{label}'")
    root_path: pathlib.Path = config_metadata.cfg_filepath.parent
    function: JobFunction
    job_tags: typing.Optional[JobTags] = Job.get_job_tags(job_config)
    os.chdir(root_path)
    function = get_job_wrapper(job_config, config_metadata.cfg_filepath)

    # get the files for all files found for this job's tags
    file_list = Job.get_job_files(file_lists, job_tags)

    if not file_list:
        # no files to work on
        log(f"WARNING: skipping job '{label}', no files for job")
        return {
            "job": (f"{label}: no files!", timedelta(0)),
            "commands": [],
        }, None

    sub_command_timings: TimingEntries = []

    def _record_sub_job_time(label: str, timing: timedelta) -> None:
        """Record timing information for sub-commands/tasks, atomically.

        For example inside of run_command() calls
        """
        sub_command_timings.append((label, timing))

    if (
        "ctx" in job_config
        and job_config["ctx"] is not None
        and "cwd" in job_config["ctx"]
        and job_config["ctx"]["cwd"]
    ):
        assert isinstance(job_config["ctx"]["cwd"], str)
        os.chdir(root_path / job_config["ctx"]["cwd"])
    else:
        os.chdir(root_path)

    start = timer()
    if config_metadata.args.verbose:
        log(f"job: running: '{Job.get_job_name(job_config)}'")
    reports: JobReturn
    try:
        reports = function(
            options=ReadOnlyInformativeDict(config_metadata.options),  # type: ignore
            file_list=file_list,
            procs=config_metadata.args.procs,
            root_path=root_path,
            verbose=config_metadata.args.verbose,
            # unpack useful data points from the job_config
            label=Job.get_job_name(job_config),
            job=job_config,
            record_sub_job_time=_record_sub_job_time,
            **kwargs,
        )
    except BaseException:  # pylint: disable=broad-exception-caught
        # log that we hit an error on this job and re-raise
        log(decorate=False)
        error(f"job: job '{Job.get_job_name(job_config)}' failed to complete!")
        # re-raise
        raise

    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    if config_metadata.args.verbose:
        log(f"job: DONE: '{label}': {time_taken}")
    this_job_timing_data: TimingEntry = (label, time_taken)
    return ({"job": this_job_timing_data, "commands": sub_command_timings}, reports)


def job_execute(
    job_config: JobConfig,
    running_jobs: typing.Dict[str, str],
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    **kwargs: typing.Any,
) -> typing.Tuple[JobTiming, JobReturn]:
    """Thin-wrapper around job_execute_inner needed for mocking in tests.

    Needed for faster tests.
    """
    this_id: str = str(uuid.uuid4())
    running_jobs[this_id] = Job.get_job_name(job_config)
    results = job_execute_inner(
        job_config,
        config_metadata,
        file_lists,
        **kwargs,
    )
    del running_jobs[this_id]
    return results
