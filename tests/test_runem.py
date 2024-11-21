import copy
import io
import multiprocessing
import os
import pathlib
import re
import sys
import typing
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import timedelta
from pprint import pprint
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

# Assuming that the modified _progress_updater function is in a module named runem
import pytest

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.runem import (
    MainReturnType,
    _main,
    _process_jobs,
    _process_jobs_by_phase,
    _update_progress,
    timed_main,
)
from runem.types.filters import FilePathListLookup
from runem.types.hooks import HookName
from runem.types.runem_config import (
    Config,
    GlobalSerialisedConfig,
    HookSerialisedConfig,
    JobConfig,
    Jobs,
    JobSerialisedConfig,
    PhaseGroupedJobs,
    UserConfigMetadata,
)
from runem.types.types_jobs import JobReturn, JobTiming
from tests.intentional_test_error import IntentionalTestError
from tests.sanitise_reports_footer import sanitise_reports_footer

DIR_REPLACEMENT_DIR: str = "[TEST_REPLACED_DIR]"


def replace_max_cores(stdout: str) -> str:
    """Replace instances of '(of X max)' with '(of [NUM CORES] max)' in a given string.

    Args:
    s (str): The original string containing '(of X max)' patterns.
    num_cores (int): The number of cores to insert into the replacement string.

    Returns:
    str: Modified string with '(of X max)' replaced by '(of [NUM CORES] max)'.
    """
    return re.sub(r"\(of \d+ max\)", "(of [NUM CORES] max)", stdout)


def _strip_reports_footer(runem_stdout: typing.List[str]) -> typing.List[str]:
    idx = runem_stdout.index("runem: reports:")
    return runem_stdout[:idx]


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
    "runem.runem.load_user_configs",
    return_value=[],
)
@patch(
    "runem.runem.load_project_config",
)
@patch(
    "runem.runem.find_files",
)
def test_runem_basic_with_config(
    find_files_mock: Mock, load_config_mock: Mock, load_config_metadata_mock: Mock
) -> None:
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("mock phase",),
            "files": [],
            "options": [],
            "min_version": None,
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
        runem_stdout: typing.List[str] = sanitise_reports_footer(buf.getvalue())
        assert [] == _strip_reports_footer(runem_stdout)

        assert [
            "runem: reports:",
            "runem (total wall-clock)  [<float>]",
            "├runem.pre-build          [<float>]",
            "└runem.run-phases         [<float>]",
            " └mock phase (user-time)  [<float>]",
            "runem: DONE: runem took: <float>, saving you <float>, without runem you "
            "would have waited <float>",
            "",
        ] == runem_stdout
    load_config_metadata_mock.assert_called_once()


@patch(
    "runem.runem.load_user_configs",
    return_value=[],
)
@patch(
    "runem.runem.load_project_config",
)
@patch(
    "runem.runem.find_files",
)
def test_runem_basic_with_config_no_options(
    find_files_mock: Mock,
    load_config_mock: Mock,
    load_config_metadata_mock: Mock,
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
        runem_stdout = buf.getvalue()
        assert [
            "runem: reports:",
            "runem (total wall-clock)  [<float>]",
            "├runem.pre-build          [<float>]",
            "└runem.run-phases         [<float>]",
            " └mock phase (user-time)  [<float>]",
            "runem: DONE: runem took: <float>, saving you <float>, without runem you "
            "would have waited <float>",
            "",
        ] == sanitise_reports_footer(runem_stdout)


MOCK_JOB_EXECUTE_INNER_RET: typing.Tuple[JobTiming, JobReturn] = (
    {"job": ("mocked job run", timedelta(0)), "commands": []},
    None,
)

MOCK_USER_LOCAL_HOOK: HookSerialisedConfig = {
    "hook": {
        "command": "echo 'mock user local hook'",
        "hook_name": HookName.ON_EXIT,
    }
}

MOCK_USER_HOME_DIR_HOOK: HookSerialisedConfig = {
    "hook": {
        "command": "echo 'mock user home-dir hook'",
        "hook_name": HookName.ON_EXIT,
    }
}

MOCK_USER_LOCAL_CONFIG: Config = [
    MOCK_USER_LOCAL_HOOK,
]
MOCK_USER_HOME_DIR_CONFIG: Config = [
    MOCK_USER_HOME_DIR_HOOK,
]

MOCK_USER_CONFIGS_METADATA: UserConfigMetadata = [
    (MOCK_USER_LOCAL_CONFIG, pathlib.Path("local-user-config.yml")),
    (MOCK_USER_HOME_DIR_CONFIG, pathlib.Path("local-user-home-dir-config.yml")),
]


@patch(
    "runem.runem.load_user_configs",
    return_value=MOCK_USER_CONFIGS_METADATA,
)
@patch(
    "runem.runem.load_project_config",
)
@patch(
    "runem.runem.find_files",
)
@patch(
    # patch the inner call that is NOT serialised by multiprocessing
    "runem.job_execute.job_execute_inner",
    return_value=MOCK_JOB_EXECUTE_INNER_RET,
)
def _run_full_config_runem(
    job_runner_mock: Mock,
    find_files_mock: Mock,
    load_config_mock: Mock,
    load_config_metadata_mock: Mock,
    runem_cli_switches: typing.List[str],
    add_verbose_switch: bool = True,
    add_command_one_liner: bool = True,
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
            "min_version": None,
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
    minimal_command_config: JobSerialisedConfig = {
        "job": {
            "command": 'echo "hello world!"',
        }
    }
    command_config: JobSerialisedConfig = {
        "job": {
            "command": 'echo "hello world!"',
            "label": "hello world",
            "when": {
                "phase": "dummy phase 2",
                "tags": set(
                    (
                        "dummy tag 1",
                        "dummy tag 2",
                    )
                ),
            },
        }
    }
    full_config: Config = [
        global_config,
        job_config_1,
        job_config_2,
        command_config,
    ]

    if add_command_one_liner:
        full_config.append(
            minimal_command_config,
        )
    minimal_file_lists = defaultdict(list)
    minimal_file_lists["mock phase"].append(pathlib.Path("/test") / "dummy" / "path")
    mocked_config_path = pathlib.Path(__file__).parent / ".runem.yml"
    load_config_mock.return_value = (full_config, mocked_config_path)
    find_files_mock.return_value = minimal_file_lists
    error_raised: typing.Optional[BaseException] = None
    argv: typing.List[str] = [
        "runem_exec",
        *runem_cli_switches,
    ]
    if add_verbose_switch:
        argv.append("--verbose")

    with io.StringIO() as buf, redirect_stdout(buf):
        # amend the args to have the exec at 0 as expected by argparse
        try:
            timed_main(argv)
        except BaseException as err:  # pylint: disable=broad-exception-caught
            error_raised = err
        runem_stdout = buf.getvalue()
    # normalise the output
    runem_stdout_lines: typing.List[str] = replace_max_cores(
        # replace the config path as it's different on different systems
        runem_stdout.replace(str(mocked_config_path), "[CONFIG PATH]")
    ).split("\n")
    # job_runner_mock.assert_called()
    got_to_reports: typing.Optional[int] = None
    try:
        got_to_reports = runem_stdout_lines.index("runem: reports:")
    except ValueError:
        pass

    if got_to_reports is not None:
        # truncate the stdout up to where the reports are logged
        runem_stdout_lines = runem_stdout_lines[:got_to_reports]
    return runem_stdout_lines, error_raised


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_with_full_config(verbosity: bool) -> None:
    """End-2-end test with a full config."""
    runem_cli_switches: typing.List[str] = []  # default switches/behaviour
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches,
        add_verbose_switch=verbosity,
    )
    if error_raised is not None:  # pragma: no cover
        print("\n".join(runem_stdout))
        raise error_raised  # re-raise the error that shouldn't have been raised

    if not verbosity:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
            (
                "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
        ]
    else:
        assert [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            "runem: will run 2 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
            "runem: will run 2 jobs for phase 'dummy phase 2'",
            "runem: \t'dummy job label 2', 'hello world'",
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
            "runem: Running Phase dummy phase 2",
            (
                "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
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
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    assert [
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 2 jobs for phase 'dummy phase 1'",
        "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
        "runem: will run 2 jobs for phase 'dummy phase 2'",
        "runem: \t'dummy job label 2', 'hello world'",
        "runem: Running Phase dummy phase 1",
        "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) processing 2 jobs",
        "runem: Running Phase dummy phase 2",
        "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) processing 2 jobs",
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
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    assert [
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 2 jobs for phase 'dummy phase 1'",
        "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
        "runem: skipping phase 'dummy phase 2'",
        "runem: Running Phase dummy phase 1",
        (
            "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
            "processing 2 jobs"
        ),
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

    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    assert runem_stdout == [
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "runem: will run 2 jobs for phase 'dummy phase 1'",
        "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
        "runem: skipping phase 'dummy phase 2'",
        "runem: Running Phase dummy phase 1",
        (
            "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
            "processing 2 jobs"
        ),
    ]


def _replace_whitespace_with_new_line(input_string: str) -> str:
    """Replaces all whitespace with a single new line."""
    return re.sub(r"\s+", "\n", input_string)


def _remove_first_line_and_split_along_whitespace(
    input_string: str,
) -> typing.List[str]:
    """Because of how argparse prints help, we need to conform it.

    To conform it we replace all whitespace with a single new-line and then split it
    into a list of strings
    """
    lines: typing.List[str] = input_string.split("\n")

    # remove the usage line as it is something like one of the following,
    # depending on whether we're running in xdist(threaded) or single-threaded
    # contexts:
    # usage: __main__.py [-h] [--jobs JOBS [JOBS ...]]
    # usage: -c [-h] [--jobs JOBS [JOBS ...]]
    index_of_usage_lines: typing.Tuple[int, ...] = (1, 9)
    usage_line: typing.Optional[str] = None
    for index_of_usage_line in index_of_usage_lines:  # pragma: no cover
        usage_line_candidate: str = lines[index_of_usage_line]
        if "usage:" in usage_line_candidate:
            usage_line = usage_line_candidate
            break
    if usage_line is None:  # pragma: no cover
        pprint(lines)
        raise RuntimeError("test setup failure, 'usage' line =NOT found in stdout")
    first_brace: int = usage_line.index("[")
    usage_line = usage_line[first_brace:]
    lines[index_of_usage_line] = usage_line

    first_line_edited: str = "\n".join(lines)
    conformed_whitespace: str = _replace_whitespace_with_new_line(first_line_edited)
    as_list: typing.List[str] = conformed_whitespace.split("\n")
    return as_list


def _conform_help_output(help_output: typing.List[str]) -> str:
    # we have to remove the run-dir for root_dir from the output
    runem_stdout_str: str = (
        "\n".join(help_output)
        .replace(str(pathlib.Path(__file__).parent), DIR_REPLACEMENT_DIR)
        .replace(
            f"({os.cpu_count()} cores available)",
            "([TEST_REPLACED_CORES] cores available)",
        )
        .replace("options:", "[TEST_REPLACED_OPTION_HEADER]")
        .replace("optional arguments:", "[TEST_REPLACED_OPTION_HEADER]")
    )
    assert runem_stdout_str
    return runem_stdout_str


@patch(
    "runem.command_line._get_config_dir",
    return_value=DIR_REPLACEMENT_DIR,
)
def test_runem_help(
    mock_get_config_dir: mock.MagicMock,
) -> None:
    """End-2-end test check that the help-output hasn't *unexpectedly* changed.

    As we build features we want to ensure that the help output stays consistent as we
    leverage the argparse system to generate the help for a specific .runem.yml config
    """
    # Ensure we get fixed-width output.
    os.environ["RUNEM_FIXED_HELP_WIDTH"] = "1"
    runem_cli_switches: typing.List[str] = ["--help"]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches,
        add_verbose_switch=False,
    )
    assert runem_stdout
    assert error_raised

    runem_stdout_str: str = _conform_help_output(runem_stdout)

    # can't cover code for multiple versions of python
    version_str: str
    if sys.version_info < (3, 11):  # pragma: no cover
        version_str = "3.10"
    else:  # pragma: no cover
        # above 3.11 seems to be stable, for now at least
        version_str = "3.11"
        # version_str = f"{sys.version_info.major}.{sys.version_info.minor}"

    # grab the expected output
    help_dump: pathlib.Path = (
        pathlib.Path(__file__).parent / "data" / f"help_output.{version_str}.txt"
    ).absolute()
    if os.environ.get("RUNEM_TEST_WRITE_HELP", False):  # pragma: no cover
        help_dump.write_text(runem_stdout_str)

    # we have to strip all whitespace as help adapts to the terminal width
    previous_help_content = help_dump.read_text()
    stripped_expected_help_output: typing.List[str] = (
        _remove_first_line_and_split_along_whitespace(previous_help_content)
    )
    stripped_actual_help_output: typing.List[str] = (
        _remove_first_line_and_split_along_whitespace(runem_stdout_str)
    )
    assert stripped_expected_help_output == stripped_actual_help_output, (
        f"{'<' * 100}\n{runem_stdout_str}\n"
        f"{'=' * 100}{previous_help_content}\n"
        f"{'>' * 100}\n"
    )
    mock_get_config_dir.assert_called_once()


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "switch_to_test",
    [
        "--version",
        "-v",
    ],
)
def test_runem_version(switch_to_test: str, verbosity: bool) -> None:
    """End-2-end test check that the --version switch works."""
    runem_cli_switches: typing.List[str] = [
        switch_to_test,
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches,
        add_command_one_liner=False,
        add_verbose_switch=verbosity,
    )
    assert runem_stdout
    assert error_raised

    # grab the expected output
    version_file: pathlib.Path = (
        pathlib.Path(__file__).parent.parent / "runem" / "VERSION"
    ).absolute()

    expected_version_output: typing.List[str] = [version_file.read_text().strip(), ""]
    if verbosity:
        expected_version_output = [
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'",
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'",
        ] + expected_version_output

    assert runem_stdout == expected_version_output


def test_runem_root_show() -> None:
    """End-2-end test check that the --root-show switch works."""
    switch_to_test: str = "--root-show"
    runem_cli_switches: typing.List[str] = [
        switch_to_test,
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches,
        add_command_one_liner=False,
        add_verbose_switch=False,
    )
    assert runem_stdout
    assert error_raised

    # In this test the config file is mocked o a dummy file in tests/ .
    runem_checkout_path: pathlib.Path = (pathlib.Path(__file__).parent).absolute()

    expected_version_output: typing.List[str] = [str(runem_checkout_path), ""]

    assert runem_stdout == expected_version_output


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
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        (
            "runem: ERROR: invalid job-name 'non existent job name' for "
            f"{switch_to_test}, choose from one of 'dummy job label 1', "
            "'dummy job label 2', 'echo \"hello world!\"', 'hello world'"
        ),
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
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        (
            f"runem: ERROR: invalid tag 'non existent tag' for {switch_to_test}, "
            "choose from one of 'dummy tag 1', 'dummy tag 2', "
            "'tag only on job 1', 'tag only on job 2'"
        ),
        "",
    ]


def test_runem_bad_validate_tag_exclude() -> None:
    """End-2-end test testing that '--not-tags' overrides '--tags'."""
    runem_cli_switches: typing.List[str] = [
        "--tags",
        "dummy tag 1",
        "--not-tags",
        "tag only on job 2",
    ]
    runem_stdout: typing.List[str]
    error_raised: typing.Optional[BaseException]
    (
        runem_stdout,
        error_raised,
    ) = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches,
        add_verbose_switch=True,
    )
    assert error_raised is None
    assert runem_stdout == [
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
        "runem: loaded config from [CONFIG PATH]",
        "runem: found 1 batches, 1 'mock phase' files, ",
        (
            "runem: filtering for tags 'dummy tag 1', excluding jobs with tags 'tag "
            "only on job 2'"
        ),
        "runem: will run 2 jobs for phase 'dummy phase 1'",
        "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
        (
            "runem: not running job 'dummy job label 2' because it contains the "
            "following tags: 'tag only on job 2'"
        ),
        "runem: will run 1 jobs for phase 'dummy phase 2'",
        "runem: \t'hello world'",
        "runem: Running Phase dummy phase 1",
        (
            "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
            "processing 2 jobs"
        ),
        "runem: Running Phase dummy phase 2",
        (
            "runem: Running 'dummy phase 2' with 1 workers (of [NUM CORES] max) "
            "processing 1 jobs"
        ),
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
        (
            "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
            "'dummy phase 1'"
        ),
        "runem: hooks: loading user hooks from 'local-user-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
        "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
        "runem: hooks: initialising 2 hooks",
        "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
            "user local hook'"
        ),
        (
            "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
            "user home-dir hook'"
        ),
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
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    if verbosity:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            (
                "runem: not running job 'echo \"hello world!\"' because it isn't "
                "in the list of job names. See --jobs and --not-jobs"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1'",
            (
                "runem: not running job 'dummy job label 2' because it isn't in the list "
                "of job names. See --jobs and --not-jobs"
            ),
            (
                "runem: not running job 'hello world' because it isn't in the list of job "
                "names. See --jobs and --not-jobs"
            ),
            (
                "runem: No jobs for phase 'dummy phase 2' tags 'dummy tag 1', "
                "'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 1 workers (of [NUM CORES] max) "
                "processing 1 jobs"
            ),
        ]
    else:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            (
                "runem: not running job 'echo \"hello world!\"' because it isn't in "
                "the list of job names. See --jobs and --not-jobs"
            ),
            "runem: will run 1 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1'",
            (
                "runem: not running job 'dummy job label 2' because it isn't in the list of "
                "job names. See --jobs and --not-jobs"
            ),
            (
                "runem: not running job 'hello world' because it isn't in the list of "
                "job names. See --jobs and --not-jobs"
            ),
            (
                "runem: No jobs for phase 'dummy phase 2' tags 'dummy tag 1', "
                "'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 1 workers (of [NUM CORES] max) "
                "processing 1 jobs"
            ),
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
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    if verbosity:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: filtering for tags 'tag only on job 1'",
            "runem: will run 2 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
            (
                "runem: not running job 'dummy job label 2' because it doesn't have "
                "any of the following tags: 'tag only on job 1'"
            ),
            (
                "runem: not running job 'hello world' because it doesn't have any "
                "of the following tags: 'tag only on job 1'"
            ),
            "runem: No jobs for phase 'dummy phase 2' tags 'tag only on job 1'",
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
        ]
    else:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            "runem: filtering for tags 'tag only on job 1'",
            "runem: will run 2 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
            (
                "runem: not running job 'dummy job label 2' because it doesn't have "
                "any of the following tags: 'tag only on job 1'"
            ),
            (
                "runem: not running job 'hello world' because it doesn't have any of the "
                "following tags: 'tag only on job 1'"
            ),
            "runem: No jobs for phase 'dummy phase 2' tags 'tag only on job 1'",
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
        ]


@pytest.mark.parametrize(
    # whether to allow a one liners that runs for all tags
    "one_liner",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_tag_out_filters_work(verbosity: bool, one_liner: bool) -> None:
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
        runem_cli_switches=runem_cli_switches, add_command_one_liner=one_liner
    )

    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    if one_liner:
        if verbosity:
            # one-liner + verbosity
            assert runem_stdout == [
                (
                    "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                    "'dummy phase 1'"
                ),
                "runem: hooks: loading user hooks from 'local-user-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: initialising 2 hooks",
                "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                    "user local hook'"
                ),
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                    "user home-dir hook'"
                ),
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
                "runem: will run 1 jobs for phase 'dummy phase 1'",
                "runem: \t'echo \"hello world!\"'",
                "runem: will run 2 jobs for phase 'dummy phase 2'",
                "runem: \t'dummy job label 2', 'hello world'",
                "runem: Running Phase dummy phase 1",
                (
                    "runem: Running 'dummy phase 1' with 1 workers (of [NUM CORES] max) "
                    "processing 1 jobs"
                ),
                "runem: Running Phase dummy phase 2",
                (
                    "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                    "processing 2 jobs"
                ),
            ]
        else:
            # one-liner + no-verbosity
            assert runem_stdout == [
                (
                    "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                    "'dummy phase 1'"
                ),
                "runem: hooks: loading user hooks from 'local-user-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: initialising 2 hooks",
                "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                    "user local hook'"
                ),
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                    "user home-dir hook'"
                ),
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
                "runem: will run 1 jobs for phase 'dummy phase 1'",
                "runem: \t'echo \"hello world!\"'",
                "runem: will run 2 jobs for phase 'dummy phase 2'",
                "runem: \t'dummy job label 2', 'hello world'",
                "runem: Running Phase dummy phase 1",
                (
                    "runem: Running 'dummy phase 1' with 1 workers (of [NUM CORES] max) "
                    "processing 1 jobs"
                ),
                "runem: Running Phase dummy phase 2",
                (
                    "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                    "processing 2 jobs"
                ),
            ]
    else:
        if verbosity:
            # no-one-liner + verbosity
            assert runem_stdout == [
                "runem: hooks: loading user hooks from 'local-user-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: initialising 2 hooks",
                "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                    "user local hook'"
                ),
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                    "user home-dir hook'"
                ),
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
                    "runem: No jobs for phase 'dummy phase 1' tags 'dummy tag 1', "
                    "'dummy tag 2', 'tag only on job 2'"
                ),
                "runem: will run 2 jobs for phase 'dummy phase 2'",
                "runem: \t'dummy job label 2', 'hello world'",
                "runem: Running Phase dummy phase 2",
                (
                    "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                    "processing 2 jobs"
                ),
            ]
        else:
            # no-one-liner + no-verbosity
            assert runem_stdout == [
                "runem: hooks: loading user hooks from 'local-user-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
                "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
                "runem: hooks: initialising 2 hooks",
                "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                    "user local hook'"
                ),
                (
                    "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                    "user home-dir hook'"
                ),
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
                    "runem: No jobs for phase 'dummy phase 1' tags 'dummy tag 1', "
                    "'dummy tag 2', 'tag only on job 2'"
                ),
                "runem: will run 2 jobs for phase 'dummy phase 2'",
                "runem: \t'dummy job label 2', 'hello world'",
                "runem: Running Phase dummy phase 2",
                (
                    "runem: Running 'dummy phase 2' with 2 workers (of [NUM CORES] max) "
                    "processing 2 jobs"
                ),
            ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_tag_out_filters_work_all_tags(verbosity: bool) -> None:
    """End-2-end test removing all tags in config.

    # TODO: assert that the tags in the runem_cli_switches match all tags in the config.
    """
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
        runem_cli_switches=runem_cli_switches,
        add_verbose_switch=False,
        add_command_one_liner=False,
    )
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    if verbosity:
        assert runem_stdout == [
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
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
            (
                "runem: not running job 'hello world' because it doesn't have any of the "
                "following tags: "
            ),
            "runem: No jobs for phase 'dummy phase 2' tags ",
        ]
    else:
        assert runem_stdout == [
            # "runem: found 1 batches, 1 'mock phase' files, ",
            # (
            #     "runem: excluding jobs with tags 'dummy tag 1', 'dummy tag 2', "
            #     "'tag only on job 1', 'tag only on job 2'"
            # ),
            # "runem: No jobs for phase 'dummy phase 1' tags ",
            # "runem: No jobs for phase 'dummy phase 2' tags ",
        ]


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
def test_runem_phase_filters_work(verbosity: bool) -> None:
    """End-2-end test filtering to a single phase."""
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
    if error_raised is not None:  # pragma: no cover
        raise error_raised  # re-raise the error that shouldn't have been raised

    if verbosity:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', 'tag only on job 1', "
                "'tag only on job 2'"
            ),
            "runem: will run 2 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
            "runem: skipping phase 'dummy phase 2'",
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
        ]
    else:
        assert runem_stdout == [
            (
                "runem: WARNING: no phase found for 'echo \"hello world!\"', using "
                "'dummy phase 1'"
            ),
            "runem: hooks: loading user hooks from 'local-user-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: loading user hooks from 'local-user-home-dir-config.yml'",
            "runem: hooks:\tadded 1 user hooks for 'HookName.ON_EXIT'",
            "runem: hooks: initialising 2 hooks",
            "runem: hooks:\tinitialising 2 hooks for 'HookName.ON_EXIT'",
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 1: echo 'mock "
                "user local hook'"
            ),
            (
                "runem: hooks: registered hook for 'HookName.ON_EXIT', have 2: echo 'mock "
                "user home-dir hook'"
            ),
            "runem: loaded config from [CONFIG PATH]",
            "runem: found 1 batches, 1 'mock phase' files, ",
            (
                "runem: filtering for tags 'dummy tag 1', 'dummy tag 2', "
                "'tag only on job 1', 'tag only on job 2'"
            ),
            "runem: will run 2 jobs for phase 'dummy phase 1'",
            "runem: \t'dummy job label 1', 'echo \"hello world!\"'",
            "runem: skipping phase 'dummy phase 2'",
            "runem: Running Phase dummy phase 1",
            (
                "runem: Running 'dummy phase 1' with 2 workers (of [NUM CORES] max) "
                "processing 2 jobs"
            ),
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


@pytest.mark.parametrize(
    # parametrize the spinner logic so we hit the various states where we use
    # 'halo' and where we don't.
    "show_spinner",
    [
        True,
        False,
    ],
)
def test_progress_updater_with_running_jobs(
    mock_sleep: Mock,
    show_spinner: bool,
) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": "running", "job2": "pending"}
    completed_jobs: typing.Dict[str, str] = {}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            completed_jobs,
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
            show_spinner=show_spinner,
        )
    mock_sleep.assert_called()


def test_progress_updater_with_running_jobs_and_10_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": "running", "job2": "pending"}
    completed_jobs: typing.Dict[str, str] = {}
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
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            completed_jobs,
            all_jobs=all_jobs,
            is_running=manager.Value("b", True),
            num_workers=1,
            show_spinner=False,
        )
    mock_sleep.assert_called()


def test_progress_updater_without_running_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {}
    completed_jobs: typing.Dict[str, str] = {}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            completed_jobs,
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
            show_spinner=False,
        )
    mock_sleep.assert_called()


def test_progress_updater_with_empty_running_jobs(mock_sleep: Mock) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": ""}
    completed_jobs: typing.Dict[str, str] = {}
    with pytest.raises(SleepCalledError), multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            completed_jobs,
            all_jobs=[],
            is_running=manager.Value("b", True),
            num_workers=1,
            show_spinner=False,
        )
    mock_sleep.assert_called()


@pytest.mark.parametrize(
    # parametrize the spinner logic so we hit the various states where we use
    # 'halo' and where we don't.
    "show_spinner",
    [
        True,
        False,
    ],
)
def test_progress_updater_with_false(show_spinner: bool) -> None:
    running_jobs: typing.Dict[str, str] = {"job1": ""}
    with multiprocessing.Manager() as manager:
        _update_progress(
            "dummy label",
            running_jobs,
            {},
            [],
            manager.Value("b", False),
            1,
            show_spinner=show_spinner,
        )


def gen_dummy_config_metadata() -> ConfigMetadata:
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            "dummy tag": {
                "tag": "dummy tag",
                "regex": ".*1.txt",  # should match just one file
            }
        },
        hook_manager=MagicMock(),
        jobs=defaultdict(list),
        all_job_names=set(),
        all_job_phases=set(),
        all_job_tags=set(),
    )
    config_metadata.set_cli_data(
        args=Namespace(verbose=False, procs=1),
        jobs_to_run=set(),  # JobNames,
        phases_to_run=set(),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )
    return config_metadata


DUMMY_MAIN_RETURN: MainReturnType = (
    gen_dummy_config_metadata(),  # ConfigMetadata,
    {},  # job_run_metadatas,
    IntentionalTestError(),
)


@patch(
    "runem.runem._main",
    return_value=DUMMY_MAIN_RETURN,
)
def test_runem_re_raises_after_reporting(
    main_mock: Mock,
) -> None:
    with pytest.raises(IntentionalTestError):
        timed_main([])


@pytest.mark.parametrize(
    "verbosity",
    [
        True,
        False,
    ],
)
@patch("runem.runem._process_jobs", return_value=IntentionalTestError())
def test_process_jobs_by_phase_early_exits_with_exceptions(
    mock_process_jobs: Mock,
    verbosity: bool,
) -> None:
    job_phase_1_raises: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_config",
        },
        "label": "a job that should be attempted",
        "when": {
            "phase": "dummy phase 1",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                )
            ),
        },
    }
    job_phase_2_not_executed: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_config",
        },
        "label": "not executed because of previous failure",
        "when": {
            "phase": "dummy phase 1",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                )
            ),
        },
    }

    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    jobs_by_phase.update(
        {
            "dummy phase 1": [job_phase_1_raises],
            "dummy phase 2": [job_phase_2_not_executed],
        }
    )

    all_job_names = (
        "not executed because of previous failure",
        "a job that should be attempted",
    )
    all_phase_names = (
        "dummy phase 1",
        "dummy phase 2",
    )
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=all_phase_names,
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        hook_manager=MagicMock(),
        jobs=jobs_by_phase,
        all_job_names=set(all_job_names),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
        # global_config,
        # job_phase_2_not_executed,
        # job_phase_1_raises,
    )

    config_metadata.set_cli_data(
        args=Namespace(verbose=verbosity, procs=1),
        jobs_to_run=set(all_job_names),  # JobNames,
        phases_to_run=set(all_phase_names),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]

    with io.StringIO() as buf, redirect_stdout(buf):
        error: typing.Optional[BaseException] = _process_jobs_by_phase(
            config_metadata=config_metadata,  # ConfigMetadata,
            file_lists=file_lists,  # FilePathListLookup,
            filtered_jobs_by_phase=jobs_by_phase,  # PhaseGroupedJobs,
            in_out_job_run_metadatas={},  # JobRunMetadatasByPhase,
            show_spinner=False,
        )
        runem_stdout = buf.getvalue().split("\n")
    assert mock_process_jobs.call_count == 1
    assert isinstance(error, IntentionalTestError)
    if not verbosity:
        assert runem_stdout == [
            "",
        ]
    else:
        assert runem_stdout == [
            "runem: Running Phase dummy phase 1",
            "runem: ERROR: running phase dummy phase 1: aborting run",
            "",
        ]


@patch("runem.runem.multiprocessing.Pool", side_effect=IntentionalTestError())
def test_process_jobs_early_exits_with_exceptions(
    mock_process_jobs: Mock,
) -> None:
    job_phase_1_raises: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_config",
        },
        "label": "a job that should be attempted",
        "when": {
            "phase": "dummy phase 1",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                )
            ),
        },
    }
    job_phase_2_not_executed: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_config",
        },
        "label": "not executed because of previous failure",
        "when": {
            "phase": "dummy phase 1",
            "tags": set(
                (
                    "dummy tag 1",
                    "dummy tag 2",
                )
            ),
        },
    }

    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    jobs_by_phase.update(
        {
            "dummy phase 1": [job_phase_1_raises],
            "dummy phase 2": [job_phase_2_not_executed],
        }
    )

    all_job_names = (
        "not executed because of previous failure",
        "a job that should be attempted",
    )
    all_phase_names = (
        "dummy phase 1",
        "dummy phase 2",
    )
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(__file__),
        phases=all_phase_names,
        options_config=tuple(),
        file_filters={
            # "dummy tag": {
            #     "tag": "dummy tag",
            #     "regex": ".*1.txt",  # should match just one file
            # }
        },
        hook_manager=MagicMock(),
        jobs=jobs_by_phase,
        all_job_names=set(all_job_names),
        all_job_phases=set(("dummy phase 1",)),
        all_job_tags=set(
            (
                "dummy tag 2",
                "dummy tag 1",
            )
        ),
        # global_config,
        # job_phase_2_not_executed,
        # job_phase_1_raises,
    )

    config_metadata.set_cli_data(
        args=Namespace(verbose=True, procs=1),
        jobs_to_run=set(all_job_names),  # JobNames,
        phases_to_run=set(all_phase_names),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )

    file_lists: FilePathListLookup = defaultdict(list)
    file_lists["dummy tag"] = [__file__]

    with io.StringIO() as buf, redirect_stdout(buf):
        error: typing.Optional[BaseException] = _process_jobs(
            config_metadata=config_metadata,  # ConfigMetadata,
            file_lists=file_lists,  # FilePathListLookup,
            in_out_job_run_metadatas=defaultdict(list),  # JobRunMetadatasByPhase,
            phase="dummy phase 1",
            jobs=[job_phase_1_raises],  # Jobs
            show_spinner=False,
        )
        runem_stdout = buf.getvalue().split("\n")
    assert mock_process_jobs.call_count == 1
    assert isinstance(error, IntentionalTestError)
    assert runem_stdout == [
        "runem: Running 'dummy phase 1' with 1 workers (of 1 max) processing 1 jobs",
        "",
    ]


@patch("runem.runem._determine_run_parameters")
@patch(
    "runem.runem.find_files", return_value=[]
)  # testing when find_files returns empty
def test_main_handles_no_files(
    mock_find_files: MagicMock, mock__determine_run_parameters: MagicMock
) -> None:
    class MockCfg:
        def __init__(self) -> None:
            self.cfg_filepath = pathlib.Path(__file__)

    mock__determine_run_parameters.return_value = MockCfg()
    with io.StringIO() as buf, redirect_stdout(buf):
        _main([])
        runem_stdout = buf.getvalue().split("\n")

    mock_find_files.assert_called_once_with(mock__determine_run_parameters.return_value)
    mock__determine_run_parameters.assert_called_once_with([])
    assert runem_stdout == [
        "runem: WARNING: no files found",
        "",
    ]
