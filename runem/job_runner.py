import argparse
import inspect
import os
import pathlib
import typing
from datetime import timedelta
from timeit import default_timer as timer

from runem.job_function_python import get_job_function
from runem.types import (
    FilePathList,
    FilePathListLookup,
    JobConfig,
    JobReturn,
    JobTags,
    Options,
)


def job_runner(
    job_config: JobConfig,
    cfg_filepath: pathlib.Path,
    args: argparse.Namespace,
    file_lists: FilePathListLookup,
    options: Options,
) -> typing.Tuple[typing.Tuple[str, timedelta], JobReturn]:
    """Wrapper for running a job inside a sub-process.

    Returns the time information and any reports the job generated
    """
    label = job_config["label"]
    if args.verbose:
        print(f"START: {label}")
    root_path: pathlib.Path = cfg_filepath.parent
    function: typing.Callable
    job_tags: JobTags = set(job_config["when"]["tags"])
    os.chdir(root_path)
    function = get_job_function(job_config, cfg_filepath)

    # get the files for all files found for this job's tags
    file_list: FilePathList = []
    for tag in job_tags:
        if tag in file_lists:
            file_list.extend(file_lists[tag])

    if not file_list:
        # no files to work on
        print(f"WARNING: skipping job '{label}', no files for job")
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
    if args.verbose:
        print(f"job: running {job_config['label']}")
    reports: JobReturn
    if "args" in func_signature.parameters:
        reports = function(args, options, file_list)
    else:
        reports = function(
            options=options,  # type: ignore
            file_list=file_list,  # type: ignore
            procs=args.procs,
            root_path=root_path,
            verbose=args.verbose,
            **job_config,
        )
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    if args.verbose:
        print(f"DONE: {label}: {time_taken}")
    timing_data = (label, time_taken)
    return (timing_data, reports)
