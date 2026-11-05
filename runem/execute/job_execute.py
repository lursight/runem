import os
import pathlib
import typing
import uuid
from datetime import timedelta
from timeit import default_timer as timer

from runem.execute.job_wrapper import get_job_wrapper
from runem.hook.hook_args import HookArgs
from runem.job.job import Job
from runem.job.job_args import JobArgs
from runem.job.job_function import JobFunction
from runem.job.job_options.informative_dict import ReadOnlyInformativeDict
from runem.job.job_return import (
    JobReturn,
)
from runem.log import error, log, warn
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.timing import TimingEntries, TimingEntry
from runem.run_command import RunemJobError
from runem.types.common import FilePathList, JobTags
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import JobConfig, JobContextConfig, JobCwd

if typing.TYPE_CHECKING:
    from runem.config.config_metadata import ConfigMetadata


class BadDeveloperExecute(ValueError):
    """Raised when there's a developer error using the system.

    ie. a function was called in an unexpected way with an unexpected config.
    """

    pass


def _chdir_into_ctx(
    root_path: pathlib.Path,
    job_name: str,
    job_ctx: JobContextConfig,
) -> None:
    """Changes directory into the job's given context cwd"""
    cwd: typing.Optional[JobCwd] = job_ctx.get("cwd", None)
    if cwd is None:
        return
    if isinstance(cwd, typing.List):
        raise BadDeveloperExecute("Dev-error: Impossible to cd into multi-cwd ctx")

    ctx_path = root_path / cwd
    if not ctx_path.exists():
        error_msg = f"job: job '{job_name}' ctx path not found! '{ctx_path}'"
        error(error_msg)
        raise ValueError(error_msg)

    try:
        os.chdir(ctx_path)
    except BaseException:  # pylint: disable=broad-exception-caught
        error(f"job: job '{job_name}' failed to chdir into ctx path! '{ctx_path}'")
        # re-raise
        raise


def job_execute_inner(
    job_config: JobConfig,
    config_metadata: "ConfigMetadata",
    file_lists: FilePathListLookup,
    metadata: HookArgs.HookData | None,
) -> typing.Tuple[JobTiming, JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label: str = Job.get_job_name(job_config)
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
        if not config_metadata.args.silent:
            warn(f"skipping job '{label}', no files for job")
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

    job_ctx: JobContextConfig | None = job_config.get("ctx", None)
    if job_ctx and "cwd" in job_ctx and job_ctx["cwd"]:
        _chdir_into_ctx(root_path, label, job_ctx)
    else:
        os.chdir(root_path)

    start = timer()
    if config_metadata.args.verbose:
        log(f"job: running: '{label}'")
    reports: JobReturn
    try:
        # Define the common args for all jobs and hooks.
        job_k_args: JobArgs = {
            "config_metadata": config_metadata,
            "file_list": file_list,
            "job": job_config,
            "label": label,
            "options": ReadOnlyInformativeDict(config_metadata.options),
            "procs": config_metadata.args.procs,
            "record_sub_job_time": _record_sub_job_time,
            "root_path": root_path,
            "verbose": config_metadata.args.verbose,
            "metadata": None,  # <- conform with JobArgs type, for now.
        }

        # We ignore the type-error for now, as this dispatch function requires
        # typing encoded into the call-side or possibly a generic `function`
        # type and branching.
        job_k_args["metadata"] = metadata  # type: ignore

        assert isinstance(function, JobFunction)
        reports = function(**job_k_args)
    except BaseException:  # pylint: disable=broad-exception-caught
        # log that we hit an error on this job and re-raise
        log(prefix=False)
        error(f"job: job '{label}' failed to complete!")
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
    config_metadata: "ConfigMetadata",
    file_lists: FilePathListLookup,
    metadata: HookArgs.HookData | None,
) -> typing.Tuple[JobTiming, JobReturn]:
    """Thin-wrapper around job_execute_inner needed for mocking in tests.

    Needed for faster tests.
    """
    this_id: str = str(uuid.uuid4())
    running_jobs[this_id] = Job.get_job_name(job_config)
    try:
        results = job_execute_inner(
            job_config,
            config_metadata,
            file_lists,
            metadata,
        )
    except RunemJobError as err:
        # The exception crosses a multiprocessing boundary. Attach the job
        # identity before it is pickled so callers can report the real job.
        err.job_name = Job.get_job_name(job_config)
        raise
    finally:
        # Always tidy-up job statuses
        completed_jobs[this_id] = running_jobs[this_id]
        del running_jobs[this_id]
    return results
