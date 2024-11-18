import io
import pathlib
import typing
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.job_execute import job_execute
from runem.run_command import RecordSubJobTimeType
from runem.types.filters import FilePathListLookup
from runem.types.runem_config import JobConfig, PhaseGroupedJobs
from tests.intentional_test_error import IntentionalTestError


def empty_function(**kwargs: typing.Any) -> None:
    """Does nothing, called by runner."""


def intentionally_raising_function(**kwargs: typing.Any) -> None:
    """Raises an error called by runner."""
    raise IntentionalTestError()


def time_recording_function(
    record_sub_job_time: typing.Optional[RecordSubJobTimeType], **kwargs: typing.Any
) -> None:
    """Does nothing, called by runner."""
    assert record_sub_job_time is not None
    record_sub_job_time("test entry", timedelta(seconds=100))
    record_sub_job_time("test entry 2", timedelta(seconds=200))


def _job_execute_and_capture_stdout(
    job_config: JobConfig,
    running_jobs: typing.Dict[str, str],
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
) -> typing.Tuple[str, typing.Optional[BaseException]]:
    """Runs job execute and asserts on stdout."""
    ret_err: typing.Optional[BaseException] = None
    with io.StringIO() as buf, redirect_stdout(buf):
        try:
            job_execute(job_config, running_jobs, {}, config_metadata, file_lists)
        except BaseException as err:  # pylint: disable=broad-exception-caught
            # capture the error and return it
            ret_err = err
        # also capture the stdout so we can inspect that as well.
        stdout: str = buf.getvalue()
    # float_less_stdout = re.sub(r"\d+\.\d+", "[FLOAT]", stdout)
    return stdout, ret_err


@pytest.fixture(name="mock_timer", autouse=True)
def create_mock_print_sleep() -> typing.Generator[None, None, None]:
    with patch("runem.job_execute.timer", return_value=0.0):  # as mock_timer
        yield


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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    stdout, _ = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert stdout == ""


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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    stdout, _ = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert stdout == (
        "runem: START: 'reformat py'\n"
        "runem: job: running: 'reformat py'\n"
        "runem: job: DONE: 'reformat py': 0:00:00\n"
    )


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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    # file_lists["dummy tag"] = [__file__]
    stdout, _ = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert stdout == (
        "runem: START: 'reformat py'\n"
        "runem: WARNING: skipping job 'reformat py', no files for job\n"
        # "runem: job: running: 'reformat py'\n"
        # "runem: job: DONE: 'reformat py': 0:00:00\n"
    )


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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    stdout, _ = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert stdout == (
        "runem: START: 'reformat py'\n"
        "runem: job: running: 'reformat py'\n"
        "runem: job: DONE: 'reformat py': 0:00:00\n"
    )


def test_job_execute_with_raising_func() -> None:
    """Tests that the output is sane on a job-function-raise.

    Aka a job-function throw.

    This test should show that it is the Python exception-handling code that
    repeats output, not the run'em code.

    FIXME: this contains a lot of copy-pasted code from above.
    """
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "intentionally_raising_function",
        },
        "label": "intentionally throwing",
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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]

    stdout, err = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert isinstance(err, IntentionalTestError)
    assert stdout.split("\n") == [
        "runem: START: 'intentionally throwing'",
        "runem: job: running: 'intentionally throwing'",
        "",
        "runem: ERROR: job: job 'intentionally throwing' failed to complete!",
        "",
    ]


def test_job_execute_time_recording_function() -> None:
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "time_recording_function",
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
        hook_manager=MagicMock(),
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
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]
    stdout, _ = _job_execute_and_capture_stdout(
        job_config,
        {},
        config_metadata,
        file_lists,
    )
    assert stdout == ""
