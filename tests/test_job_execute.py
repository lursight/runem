import pathlib
import typing
from argparse import Namespace
from collections import defaultdict

from runem.config_metadata import ConfigMetadata
from runem.job_execute import job_execute
from runem.types import (
    FilePathList,
    FilePathListLookup,
    JobConfig,
    Options,
    PhaseGroupedJobs,
)


def empty_function(**kwargs: typing.Any) -> None:
    """Does nothing, called by runner."""


def old_style_function(
    args: Namespace, options: Options, file_list: FilePathList
) -> None:
    """Does nothing called by runner."""


def test_job_execute_basic_call() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "empty_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "dummy tag",
                    "tag not in files",
                )
            ),
        },
    }
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        job_config,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=False, procs=1),
        jobs_to_run=set((job_config["label"])),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    job_execute(job_config, {}, config_metadata, file_lists)


def test_job_execute_basic_call_verbose() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "empty_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(("dummy tag",)),
        },
    }
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        job_config,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set((job_config["label"])),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    job_execute(job_config, {}, config_metadata, file_lists)


def test_job_execute_empty_files() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "empty_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(("dummy tag",)),
        },
    }
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        job_config,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set((job_config["label"])),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    # file_lists["dummy tag"] = [__file__]
    job_execute(job_config, {}, config_metadata, file_lists)


def test_job_execute_with_ctx_cwd() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "empty_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(("dummy tag",)),
        },
        "ctx": {
            # set the cwd
            "cwd": ".",
        },
    }
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        job_config,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set((job_config["label"])),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    job_execute(job_config, {}, config_metadata, file_lists)


def test_job_execute_with_old_style_func() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "old_style_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(("dummy tag",)),
        },
        "ctx": {
            # set the cwd
            "cwd": ".",
        },
    }
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        job_config,
    ]
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=config_file_path,
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        jobs=expected_jobs,
        all_job_names=set(("dummy job label",)),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set((job_config["label"])),  # JobNames,
        phases_to_run=set(),  # ignored JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options={},  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    job_execute(job_config, {}, config_metadata, file_lists)
