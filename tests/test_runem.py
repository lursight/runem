import io
import pathlib
import typing
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from runem.runem import timed_main
from runem.types import Config, GlobalSerialisedConfig, JobSerialisedConfig


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
            "found 1 batches, 1 'mock phase' files, ",
            "skipping phase 'mock phase'",
        ] == runem_stdout[:2]


@patch(
    "runem.runem.load_config",
)
@patch(
    "runem.runem.find_files",
)
def _run_full_config_runem(
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
    assert [
        "found 1 batches, 1 'mock phase' files, ",
        "filtering for tags 'dummy tag 1', 'dummy tag 2'",
        "will run 1 jobs for phase 'dummy phase 1'",
        "\t['dummy job label 1']",
        "will run 1 jobs for phase 'dummy phase 2'",
        "\t['dummy job label 2']",
        "Running 'dummy phase 1' with 1 workers processing 1 jobs",
        "Running 'dummy phase 2' with 1 workers processing 1 jobs",
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
    assert [
        "loaded config from [CONFIG PATH]",
        "found 1 batches, 1 'mock phase' files, ",
        "filtering for tags 'dummy tag 1', 'dummy tag 2'",
        "will run 1 jobs for phase 'dummy phase 1'",
        "\t['dummy job label 1']",
        "will run 1 jobs for phase 'dummy phase 2'",
        "\t['dummy job label 2']",
        "Running Phase dummy phase 1",
        "Running 'dummy phase 1' with 1 workers processing 1 jobs",
        "Running Phase dummy phase 2",
        "Running 'dummy phase 2' with 1 workers processing 1 jobs",
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
    assert [
        "found 1 batches, 1 'mock phase' files, ",
        "filtering for tags 'dummy tag 1', 'dummy tag 2'",
        "will run 1 jobs for phase 'dummy phase 1'",
        "\t['dummy job label 1']",
        "skipping phase 'dummy phase 2'",
        "Running 'dummy phase 1' with 1 workers processing 1 jobs",
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
    assert error_raised is None
    assert runem_stdout == [
        "loaded config from [CONFIG PATH]",
        "found 1 batches, 1 'mock phase' files, ",
        "filtering for tags 'dummy tag 1', 'dummy tag 2'",
        "will run 1 jobs for phase 'dummy phase 1'",
        "\t['dummy job label 1']",
        "skipping phase 'dummy phase 2'",
        "Running Phase dummy phase 1",
        "Running 'dummy phase 1' with 1 workers processing 1 jobs",
    ]


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
    assert error_raised

    # we have to strip all whitespace as help adapts to the terminal width
    stripped_expected_help_output: str = "".join(
        [
            # "usage: __main__.py [-h] [--jobs JOBS [JOBS ...]]",
            "                   [--not-jobs JOBS_EXCLUDED [JOBS_EXCLUDED ...]]",
            "                   [--phases PHASES [PHASES ...]]",
            "                   [--not-phases PHASES_EXCLUDED [PHASES_EXCLUDED ...]]",
            "                   [--tags TAGS [TAGS ...]]",
            "                   [--not-tags TAGS_EXCLUDED [TAGS_EXCLUDED ...]]",
            "                   [--dummy-option-1---complete-option]",
            "                   [--no-dummy-option-1---complete-option]",
            "                   [--dummy-option-2---minimal]",
            "                   [--no-dummy-option-2---minimal]",
            "                   [--call-graphs | --no-call-graphs] [--procs PROCS]",
            "                   [--root ROOT_DIR] [--verbose | --no-verbose | -v]",
            "",
            "Runs the Lursight Lang test-suite",
            "",
            "options:",
            "  -h, --help            show this help message and exit",
            "  --call-graphs, --no-call-graphs",
            "  --procs PROCS, -j PROCS",
            "                        the number of concurrent test jobs to run, -1 runs "
            "all",
            "                        test jobs at the same time (8 cores available)",
            "  --root ROOT_DIR       which dir to use as the base-dir for testing, "
            "defaults",
            "                        to directory containing the config",
            "                        '/Users/frank/Development/fah_products/runem/tests'",
            "  --verbose, --no-verbose, -v",
            "",
            "jobs:",
            "  --jobs JOBS [JOBS ...]",
            "                        List of job-names to run the given jobs. Other "
            "filters",
            "                        will modify this list. Defaults to 'dummy job label",
            "                        1', 'dummy job label 2'",
            "  --not-jobs JOBS_EXCLUDED [JOBS_EXCLUDED ...]",
            "                        List of job-names to NOT run. Defaults to empty.",
            "                        Available options are: 'dummy job label 1', 'dummy "
            "job",
            "                        label 2'",
            "",
            "phases:",
            "  --phases PHASES [PHASES ...]",
            "                        Run only the phases passed in, and can be used to",
            "                        change the phase order. Phases are run in the order",
            "                        given. Defaults to 'dummy phase 1', 'dummy phase 2'.",
            "  --not-phases PHASES_EXCLUDED [PHASES_EXCLUDED ...]",
            "                        List of phases to NOT run. This option does not "
            "change",
            "                        the phase run order. Options are '['dummy phase 1',",
            "                        'dummy phase 2']'.",
            "",
            "tags:",
            "  --tags TAGS [TAGS ...]",
            "                        Only jobs with the given tags. Defaults to '['dummy",
            "                        tag 1', 'dummy tag 2']'.",
            "  --not-tags TAGS_EXCLUDED [TAGS_EXCLUDED ...]",
            "                        Removes one or more tags from the list of job tags "
            "to",
            "                        be run. Options are '['dummy tag 1', 'dummy tag "
            "2']'.",
            "",
            "job-param overrides:",
            "  --dummy-option-1---complete-option, --dummy option 1 multi alias 1, --dummy "
            "option 1 multi alias 2, -x, --dummy option alias 1",
            "                        a dummy option description",
            "  --no-dummy-option-1---complete-option, --no-dummy option 1 multi alias 1, "
            "--no-dummy option 1 multi alias 2, --no-x, --no-dummy option alias 1",
            "                        turn off a dummy option description",
            "  --dummy-option-2---minimal",
            "  --no-dummy-option-2---minimal",
            "",
        ]
    ).replace(" ", "")
    # we have to strip all whitespace as help adapts to the terminal width
    stripped_actual_help_output = "".join(runem_stdout[1:]).replace(" ", "")
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
        f"ERROR: invalid job-name 'non existent job name' for {switch_to_test}, "
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
        f"ERROR: invalid tag 'non existent tag' for {switch_to_test}, "
        "choose from one of 'dummy tag 1', 'dummy tag 2'",
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
        f"ERROR: invalid phase 'non existent phase' for {switch_to_test}, "
        "choose from one of 'dummy phase 1', 'dummy phase 2'",
        "",
    ]
