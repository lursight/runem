import inspect
import os
import pathlib
import typing
import uuid
from datetime import timedelta
from timeit import default_timer as timer

from runem.config_metadata import ConfigMetadata
from runem.job import Job
from runem.job_wrapper import get_job_wrapper
from runem.log import log
from runem.types import FilePathListLookup, JobConfig, JobFunction, JobReturn, JobTags


def job_execute_inner(
    job_config: JobConfig,
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label = Job.get_job_name(job_config)
    if config_metadata.args.verbose:
        log(f"START: {label}")
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
        return (f"{label}: no files!", timedelta(0)), None

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
    func_signature = inspect.signature(function)
    if config_metadata.args.verbose:
        log(f"job: running {Job.get_job_name(job_config)}")
    reports: JobReturn
    if "args" in func_signature.parameters:
        reports = function(  # type: ignore  # FIXME: which function do we have?
            config_metadata.args, config_metadata.options, file_list
        )
    else:
        reports = function(
            options=config_metadata.options,  # type: ignore
            file_list=file_list,
            procs=config_metadata.args.procs,
            root_path=root_path,
            verbose=config_metadata.args.verbose,
            # unpack useful data points from the job_config
            label=Job.get_job_name(job_config),
            job=job_config,
        )
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    if config_metadata.args.verbose:
        log(f"DONE: {label}: {time_taken}")
    timing_data = (label, time_taken)
    return (timing_data, reports)


def job_execute(
    job_config: JobConfig,
    running_jobs: typing.Dict[str, str],
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    """Thin-wrapper around job_execute_inner needed for mocking in tests.

    Needed for faster tests.
    """
    this_id: str = str(uuid.uuid4())
    running_jobs[this_id] = Job.get_job_name(job_config)
    results = job_execute_inner(job_config, config_metadata, file_lists)
    del running_jobs[this_id]
    return results
