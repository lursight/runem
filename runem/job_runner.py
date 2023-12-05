import inspect
import os
import pathlib
import typing
from datetime import timedelta
from timeit import default_timer as timer

from runem.config_metadata import ConfigMetadata
from runem.job_function_python import get_job_function
from runem.log import log
from runem.types import FilePathList, FilePathListLookup, JobConfig, JobReturn, JobTags


def job_runner_inner(
    job_config: JobConfig,
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label = job_config["label"]
    if config_metadata.args.verbose:
        log(f"START: {label}")
    root_path: pathlib.Path = config_metadata.cfg_filepath.parent
    function: typing.Callable
    job_tags: JobTags = set(job_config["when"]["tags"])
    os.chdir(root_path)
    function = get_job_function(job_config, config_metadata.cfg_filepath)

    # get the files for all files found for this job's tags
    file_list: FilePathList = []
    for tag in job_tags:
        if tag in file_lists:
            file_list.extend(file_lists[tag])

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
        os.chdir(root_path / job_config["ctx"]["cwd"])
    else:
        os.chdir(root_path)

    start = timer()
    func_signature = inspect.signature(function)
    if config_metadata.args.verbose:
        log(f"job: running {job_config['label']}")
    reports: JobReturn
    if "args" in func_signature.parameters:
        reports = function(config_metadata.args, config_metadata.options, file_list)
    else:
        reports = function(
            options=config_metadata.options,  # type: ignore
            file_list=file_list,  # type: ignore
            procs=config_metadata.args.procs,
            root_path=root_path,
            verbose=config_metadata.args.verbose,
            **job_config,
        )
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    if config_metadata.args.verbose:
        log(f"DONE: {label}: {time_taken}")
    timing_data = (label, time_taken)
    return (timing_data, reports)


def job_runner(
    job_config: JobConfig,
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    """Thing wrapper around job_runner_inner needed fro mocking in tests.

    Needed for faster tests.
    """
    return job_runner_inner(job_config, config_metadata, file_lists)
