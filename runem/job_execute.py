import os
import pathlib
import typing
import uuid
from datetime import timedelta
from timeit import default_timer as timer

from typing_extensions import Unpack

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import ReadOnlyInformativeDict
from runem.job import Job
from runem.job_wrapper import get_job_wrapper
from runem.log import error, log
from runem.types.common import FilePathList, JobTags
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import (
    AllKwargs,
    HookSpecificKwargs,
    JobFunction,
    JobKwargs,
    JobReturn,
    JobTiming,
    TimingEntries,
    TimingEntry,
)


def job_execute_inner(
    job_config: JobConfig,
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    **kwargs: Unpack[HookSpecificKwargs],
) -> typing.Tuple[JobTiming, JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label = Job.get_job_name(job_config)
    if config_metadata.args.verbose:
        log(f"START: '{label}'")
    root_path: pathlib.Path = config_metadata.cfg_filepath.parent
    job_tags: typing.Optional[JobTags] = Job.get_job_tags(job_config)
    os.chdir(root_path)
    function: JobFunction = get_job_wrapper(job_config, config_metadata.cfg_filepath)

    # get the files for all files found for this job's tags
    file_list: FilePathList = Job.get_job_files(file_lists, job_tags)

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
        # Define the common args for all jobs and hooks.
        job_k_args: JobKwargs = {
            "config_metadata": config_metadata,
            "file_list": file_list,
            "job": job_config,
            "label": Job.get_job_name(job_config),
            "options": ReadOnlyInformativeDict(config_metadata.options),
            "procs": config_metadata.args.procs,
            "record_sub_job_time": _record_sub_job_time,
            "root_path": root_path,
            "verbose": config_metadata.args.verbose,
        }
        # Merge in the hook-specific kwargs (if any) for situations where we are
        # calling hooks.
        all_k_args: AllKwargs = {
            **job_k_args,
            **kwargs,
        }

        assert isinstance(function, JobFunction)
        reports = function(**all_k_args)
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
    completed_jobs: typing.Dict[str, str],
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    **kwargs: Unpack[HookSpecificKwargs],
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
    completed_jobs[this_id] = running_jobs[this_id]
    del running_jobs[this_id]
    return results
