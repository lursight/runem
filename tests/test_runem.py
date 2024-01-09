import copy
import io
import multiprocessing
import os
import pathlib
import re
import typing
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import timedelta
from pprint import pprint
from unittest.mock import Mock, patch

# Assuming that the modified _progress_updater function is in a module named runem
import pytest

from runem.runem import _update_progress, timed_main
from runem.types import (
    Config,
    GlobalSerialisedConfig,
    JobConfig,
    Jobs,
    JobSerialisedConfig,
)


def _remove_x_of_y_workers_log(
    runem_stdout: typing.List[str], phase: str = "dummy phase 1"
) -> None:
    """Asserts that the 'x of y' workers text exists and in-place tries to remove it.

    This is because the number of works changes per machine.
    """
    machine_specific_job: str = (
        f"runem: Running '{phase}' with 1 workers (of "
        f"{multiprocessing.cpu_count()} max) processing 1 jobs"
    )
    # the index() call will error if the X/Z message isn't found, so we know
    # it's there, so just remove it.
    pprint(runem_stdout)
    assert machine_specific_job in runem_stdout, runem_stdout
    idx = runem_stdout.index(machine_specific_job)
    del runem_stdout[idx]


def test_runem_basic() -> None:
    """Tests new user's first call-path, when they wouldn't have a .runem.yml."""
    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(SystemExit):
            timed_main([])
        runem_stdout = buf.getvalue()

        # this is what we should see when first installing runem
        # TODO: add an on-boarding work flow
        assert "ERROR: Config not found! Looked from" in runem_stdout


@patch(
    "runem.runem.load_config",
)
@patch(
    "runem.runem.find_files",
)
def test_runem_basic_with_config(
    find_files_mock: Mock,
    load_config_mock: Mock,
) -> None:
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("mock phase",),
            "files": [],
            "options": [],
        }
    }
    empty_config: Config = [
        global_config,
    ]
    minimal_file_lists = defaultdict(list)
    minimal_file_lists["mock phase"].append(pathlib.Path("/test") / "dummy" / "path")
    load_config_mock.return_value = (empty_config, pathlib.Path())
    find_files_mock.return_value = minimal_file_lists
    with io.StringIO() as buf, redirect_stdout(buf):
        # with pytest.raises(SystemExit):
        timed_main(["--help"])
        runem_stdout = buf.getvalue().split("\n")
        assert [
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: skipping phase 'mock phase'",
        ] == runem_stdout[:2]


@patch(
    "runem.runem.load_config",
)
@patch(
    "runem.runem.find_files",
)
def test_runem_basic_with_config_no_options(
    find_files_mock: Mock,
    load_config_mock: Mock,
) -> None:
    global_config: GlobalSerialisedConfig = {
        "config": {  # type: ignore[typeddict-item]
            "phases": ("mock phase",),
            "files": [],
            # "options": [],
        }
    }
    empty_config: Config = [
        global_config,
    ]
    minimal_file_lists = defaultdict(list)
    minimal_file_lists["mock phase"].append(pathlib.Path("/test") / "dummy" / "path")
    load_config_mock.return_value = (empty_config, pathlib.Path())
    find_files_mock.return_value = minimal_file_lists
    with io.StringIO() as buf, redirect_stdout(buf):
        # with pytest.raises(SystemExit):
        timed_main(["--help"])
        runem_stdout = buf.getvalue().split("\n")
        assert [
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: skipping phase 'mock phase'",
        ] == runem_stdout[:2]


@patch(
    "runem.runem.load_config",
)
@patch(
    "runem.runem.find_files",
)
@patch(
    # patch the inner call that is NOT serialised by multiprocessing
    "runem.job_execute.job_execute_inner",
    return_value=(("mocked job run", timedelta(0)), None),
)
def _run_full_config_runem(
    job_runner_mock: Mock,
    find_files_mock: Mock,
    load_config_mock: Mock,
    runem_cli_switches: typing.List[str],
) -> typing.Tuple[typing.List[str], typing.Optional[BaseException]]:
    """A wrapper around running runem e2e tests.

    'runem_cli_switches' should be the runem args, and NOT include the executable at
    index 0.

    Returns a list of lines of terminal output
    """
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1", "dummy phase 2"),
            "files": [],
            "options": [
                {
                    "option": {
                        "default": True,
                        "desc": "a dummy option description",
                        "aliases": [
                            "dummy option 1 multi alias 1",
                            "dummy option 1 multi alias 2",
                            "x",
                        ],
                        "alias": "dummy option alias 1",
                        "name": "dummy option 1 - complete option",
                        "type": "bool",
                    }
                },
                {
                    "option": {
                        "default": True,
                        "name": "dummy option 2 - minimal",
                        "type": "bool",
                    }
                },
            ],
        }
    }
    job_config_1: JobSerialisedConfig = {
        "job": {
            "addr": {
                "file": __file__,
                "function": "test_runem_with_full_config",
            },
            "label": "dummy job label 1",
            "when": {
                "phase": "dummy phase 1",
                "tags": set(
                    (
                        "dummy tag 1",
                        "dummy tag 2",
                        "tag only on job 1",
                    )
                ),
            },
        }
    }
    job_config_2: JobSerialisedConfig = {
        "job": {
            "addr": {
                "file": __file__,
                "function": "test_runem_with_full_config",
            },
            "label": "dummy job label 2",
            "when": {
                "phase": "dummy phase 2",
                "tags": set(
                    (
                        "dummy tag 1",
                        "dummy tag 2",
                        "tag only on job 2",
                    )
                ),
            },
        }
    }
    full_config: Config = [global_config, job_config_1, job_config_2]
    minimal_file_lists = defaultdict(list)
    minimal_file_lists["mock phase"].append(pathlib.Path("/test") / "dummy" / "path")
    mocked_config_path = pathlib.Path(__file__).parent / ".runem.yml"
    load_config_mock.return_value = (full_config, mocked_config_path)
    find_files_mock.return_value = minimal_file_lists
    error_raised: typing.Optional[BaseException] = None
    with io.StringIO() as buf, redirect_stdout(buf):
        # amend the args to have the exec at 0 as expected by argsparse
        try:
            timed_main(["runem_exec", *runem_cli_switches])
        except BaseException as err:  # pylint: disable=broad-exception-caught
            error_raised = err
        runem_stdout = (
            buf.getvalue().replace(str(mocked_config_path), "[CONFIG PATH]").split("\n")
        )
    # job_runner_mock.assert_called()
    got_to_reports: typing.Optional[int] = None
    try:
        got_to_reports = runem_stdout.index("runem: reports:")
    except ValueError:
        pass

    if got_to_reports is not None:
        # truncate the stdout up to where the reports are logged
        runem_stdout = runem_stdout[:got_to_reports]
    return runem_stdout, error_raised


def test_runem_with_full_config() -> None:
    """End-2-end test with a full config."""
    runem_cli_switches: typing.List[str] = []  # default switches/behaviour
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None
    _remove_x_of_y_workers_log(runem_stdout, phase="dummy phase 1")
    _remove_x_of_y_workers_log(runem_stdout, phase="dummy phase 2")

    assert [
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 1 jobs for phase 'dummy phase 1'",
        "runem: \t['dummy job label 1']",
        "runem: will run 1 jobs for phase 'dummy phase 2'",
        "runem: \t['dummy job label 2']",
        # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        # "runem: Running 'dummy phase 2' with 1 workers processing 1 jobs",
    ] == runem_stdout


def test_runem_with_full_config_verbose() -> None:
    """End-2-end test with a full config."""
    runem_cli_switches: typing.List[str] = ["--verbose"]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None

    _remove_x_of_y_workers_log(runem_stdout, phase="dummy phase 1")
    _remove_x_of_y_workers_log(runem_stdout, phase="dummy phase 2")

    assert [
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 1 jobs for phase 'dummy phase 1'",
        "runem: \t['dummy job label 1']",
        "runem: will run 1 jobs for phase 'dummy phase 2'",
        "runem: \t['dummy job label 2']",
        "runem: Running Phase dummy phase 1",
        # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        "runem: Running Phase dummy phase 2",
        # "runem: Running 'dummy phase 2' with 1 workers processing 1 jobs",
    ] == runem_stdout


def test_runem_with_single_phase() -> None:
    """End-2-end test with a full config choosing only a single phase."""
    runem_cli_switches: typing.List[str] = ["--phases", "dummy phase 1"]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None

    _remove_x_of_y_workers_log(runem_stdout)

    assert [
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 1 jobs for phase 'dummy phase 1'",
        "runem: \t['dummy job label 1']",
        "runem: skipping phase 'dummy phase 2'",
        # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
    ] == runem_stdout


def test_runem_with_single_phase_verbose() -> None:
    """End-2-end test with a full config choosing only a single phase."""
    runem_cli_switches: typing.List[str] = ["--phases", "dummy phase 1", "--verbose"]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )

    _remove_x_of_y_workers_log(runem_stdout)

    assert error_raised is None
    assert runem_stdout == [
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 1 jobs for phase 'dummy phase 1'",
        "runem: \t['dummy job label 1']",
        "runem: skipping phase 'dummy phase 2'",
        "runem: Running Phase dummy phase 1",
        # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
    ]


def _replace_whitespace_with_new_line(input_string: str) -> str:
    """Replaces all whitespace with a single new line."""
    return re.sub(r"\s+", "\n", input_string)


def _remove_first_line_and_split_along_whitespace(
    input_string: str,
) -> typing.List[str]:
    """Because of how argsparse prints help, we need to conform it.

    To conform it we replace all whitespace with a single new-line and then split it
    into a list of strings
    """
    first_line_removed: str = "\n".join(input_string.split("\n")[1:])
    conformed_whitespace: str = _replace_whitespace_with_new_line(first_line_removed)
    as_list: typing.List[str] = conformed_whitespace.split("\n")
    return as_list


def _conform_help_output(help_output: typing.List[str]) -> str:
    # we have to remove the run-dir for root_dir from the output
    runem_stdout_str: str = (
        "\n".join(help_output)
        .replace(str(pathlib.Path(__file__).parent), "[TEST_REPLACED_DIR]")
        .replace(
            f"({os.cpu_count()} cores available)",
            "([TEST_REPLACED_CORES] cores available)",
        )
        .replace("options:", "[TEST_REPLACED_OPTION_HEADER]")
        .replace("optional arguments:", "[TEST_REPLACED_OPTION_HEADER]")
    )
    assert runem_stdout_str
    return runem_stdout_str


def test_runem_help() -> None:
    """End-2-end test with a full config choosing only a single phase."""
    runem_cli_switches: typing.List[str] = ["--help"]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert runem_stdout
    assert error_raised

    runem_stdout_str: str = _conform_help_output(runem_stdout)

    # grab the expected output
    help_dump: pathlib.Path = (
        pathlib.Path(__file__).parent / "data" / "help_output.txt"
    ).absolute()
    # help_dump.write_text(runem_stdout_str)

    # we have to strip all whitespace as help adapts to the terminal width
    stripped_expected_help_output: typing.List[
        str
    ] = _remove_first_line_and_split_along_whitespace(help_dump.read_text())
    stripped_actual_help_output: typing.List[
        str
    ] = _remove_first_line_and_split_along_whitespace(runem_stdout_str)
    assert stripped_expected_help_output == stripped_actual_help_output


@pytest.mark.parametrize(
    "switch_to_test",
    [
        "--jobs",
        "--not-jobs",
    ],
)
def test_runem_bad_validate_switch_jobs(switch_to_test: str) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        switch_to_test,
        "non existent job name",
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is not None
    assert isinstance(error_raised, SystemExit)
    assert runem_stdout == [
        f"runem: ERROR: invalid job-name 'non existent job name' for {switch_to_test}, "
        "choose from one of 'dummy job label 1', 'dummy job label 2'",
        "",
    ]


@pytest.mark.parametrize(
    "switch_to_test",
    [
        "--tags",
        "--not-tags",
    ],
)
def test_runem_bad_validate_switch_tags(switch_to_test: str) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        switch_to_test,
        "non existent tag",
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is not None
    assert isinstance(error_raised, SystemExit)
    assert runem_stdout == [
        (
            f"runem: ERROR: invalid tag 'non existent tag' for {switch_to_test}, "
            "choose from one of 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "",
    ]


@pytest.mark.parametrize(
    "switch_to_test",
    [
        "--phases",
        "--not-phases",
    ],
)
def test_runem_bad_validate_switch_phases(switch_to_test: str) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        switch_to_test,
        "non existent phase",
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is not None
    assert isinstance(error_raised, SystemExit)
    assert runem_stdout == [
        f"runem: ERROR: invalid phase 'non existent phase' for {switch_to_test}, "
        "choose from one of 'dummy phase 1', 'dummy phase 2'",
        "",
    ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_job_filters_work(verbosity: bool) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        "--jobs",
        "dummy job label 1",
    ]
    if verbosity:
        runem_cli_switches.append("--verbose")
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None

    _remove_x_of_y_workers_log(runem_stdout)

    if verbosity:
        assert runem_stdout == [
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            (
                "runem: not running job 'dummy job label 2' because it isn't in the list "
                "of job names. See --jobs and --not-jobs"
            ),
            (
                "runem: No jobs for phase 'dummy phase 2' tags 'dummy tag 1', "
                "'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: Running Phase dummy phase 1",
            # see above: "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]
    else:
        assert runem_stdout == [
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            (
                "runem: No jobs for phase 'dummy phase 2' tags 'dummy tag 1', "
                "'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            # see above: "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_tag_filters_work(verbosity: bool) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        "--tags",
        "tag only on job 1",
    ]
    if verbosity:
        runem_cli_switches.append("--verbose")
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None

    _remove_x_of_y_workers_log(runem_stdout)

    if verbosity:
        assert runem_stdout == [
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: filtering for tags 'tag only on job 1'",
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            (
                "runem: not running job 'dummy job label 2' because it doesn't have any of the "
                "following tags: 'tag only on job 1'"
            ),
            "runem: No jobs for phase 'dummy phase 2' tags 'tag only on job 1'",
            "runem: Running Phase dummy phase 1",
            # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]
    else:
        assert runem_stdout == [
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: filtering for tags 'tag only on job 1'",
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            "runem: No jobs for phase 'dummy phase 2' tags 'tag only on job 1'",
            # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_tag_out_filters_work(verbosity: bool) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        "--not-tags",
        "tag only on job 1",
    ]
    if verbosity:
        runem_cli_switches.append("--verbose")
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )

    _remove_x_of_y_workers_log(runem_stdout, phase="dummy phase 2")

    assert error_raised is None
    if verbosity:
        assert runem_stdout == [
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 2', excluding jobs with tags 'tag only on job 1'"
            ),
            (
                "runem: not running job 'dummy job label 1' because it contains "
                "the following tags: 'tag only on job 1'"
            ),
            (
                "runem: No jobs for phase 'dummy phase 1' tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 2'",
            "runem: \t['dummy job label 2']",
            "runem: Running Phase dummy phase 2",
            # "runem: Running 'dummy phase 2' with 1 workers processing 1 jobs",
        ]
    else:
        assert runem_stdout == [
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', 'tag only on job 2', "
                "excluding jobs with tags 'tag only on job 1'"
            ),
            (
                "runem: No jobs for phase 'dummy phase 1' tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 2'",
            "runem: \t['dummy job label 2']",
            # "runem: Running 'dummy phase 2' with 1 workers processing 1 jobs",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_tag_out_filters_work_all_tags(verbosity: bool) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        "--not-tags",
        "tag only on job 1",
        "tag only on job 2",
        "dummy tag 1",
        "dummy tag 2",
    ]
    if verbosity:
        runem_cli_switches.append("--verbose")
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None
    if verbosity:
        assert runem_stdout == [
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: excluding jobs with tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            (
                "runem: not running job 'dummy job label 1' because it doesn't have any of "
                "the following tags: "
            ),
            "runem: No jobs for phase 'dummy phase 1' tags ",
            (
                "runem: not running job 'dummy job label 2' because it doesn't have any of "
                "the following tags: "
            ),
            "runem: No jobs for phase 'dummy phase 2' tags ",
        ]
    else:
        assert runem_stdout == [
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: excluding jobs with tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            "runem: No jobs for phase 'dummy phase 1' tags ",
            "runem: No jobs for phase 'dummy phase 2' tags ",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_phase_filters_work(verbosity: bool) -> None:
    """End-2-end test failing validation on non existent job-names."""
    runem_cli_switches: typing.List[str] = [
        "--phases",
        "dummy phase 1",
    ]
    if verbosity:
        runem_cli_switches.append("--verbose")
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
    assert error_raised is None

    _remove_x_of_y_workers_log(runem_stdout)

    if verbosity:
        assert runem_stdout == [
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            "runem: skipping phase 'dummy phase 2'",
            "runem: Running Phase dummy phase 1",
            # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]
    else:
        assert runem_stdout == [
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t['dummy job label 1']",
            "runem: skipping phase 'dummy phase 2'",
            # "runem: Running 'dummy phase 1' with 1 workers processing 1 jobs",
        ]


class SleepCalledError(ValueError):
    """Thrown when the sleep function is called to stop the infinite loop."""


@pytest.fixture(name="mock_sleep")
def create_mock_print_sleep() -> typing.Generator[typing.Tuple[Mock, Mock], None, None]:
    call_count = 0

    def custom_side_effect(*args: typing.Any, **kwargs: typing.Any) -> float:
        nonlocal call_count
        if call_count < 3:
            call_count += 1
            return 0.1  # Return a valid value for the first call
        raise SleepCalledError("Mocked sleep error on the second call")

    with patch("time.sleep", side_effect=custom_side_effect) as mock_sleep:
        yield mock_sleep


def test_progress_updater_with_running_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": "running", "job2": "pending"}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            seen_jobs=[],
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
        )
    mock_sleep.assert_called()


def test_progress_updater_with_running_jobs_and_10_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": "running", "job2": "pending"}
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_job_config",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "py",
                    "format",
                )
            ),
        },
    }
    all_jobs: Jobs = []
    for idx in range(10):
        job_config = copy.copy(job_config)
        job_config["label"] = f'{job_config["label"]} {idx}'
        all_jobs.append(job_config)
    pprint(all_jobs)
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            seen_jobs=[],
            all_jobs=all_jobs,
            is_running=manager.Value("b", True),
            num_workers=1,
        )
    mock_sleep.assert_called()


def test_progress_updater_without_running_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            seen_jobs=[],
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
        )
    mock_sleep.assert_called()


def test_progress_updater_with_empty_running_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": ""}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            seen_jobs=[],
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
        )
    mock_sleep.assert_called()


def test_progress_updater_with_false() -> None:
    running_jobs: typing.Dict[str, str] = {"job1": ""}
    with multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label", running_jobs, [], [], manager.Value("b", False), 1
        )
