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
) -> typing.List[str]:
    """A wrapper around running runem e2e tests.

    'runem_cli_switches' should be the runem args, and NOT include the executable at
    index 0.

    Returns a list of lines of terminal output
    """
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1", "dummy phase 2"),
            "files": [],
            "options": [],
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
    with io.StringIO() as buf, redirect_stdout(buf):
        # amend the args to have the exec at 0 as expected by argsparse
        timed_main(["runem_exec", *runem_cli_switches])
        runem_stdout = (
            buf.getvalue().replace(str(mocked_config_path), "[CONFIG PATH]").split("\n")
        )
    # truncate the stdout up to where the reports are logged
    runem_stdout = runem_stdout[: runem_stdout.index("runem: reports:")]
    return runem_stdout


def test_runem_with_full_config() -> None:
    """End-2-end test with a full config."""
    runem_cli_switches: typing.List[str] = []  # default switches/behaviour
    runem_stdout: typing.List[
        str
    ] = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
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
    runem_stdout: typing.List[
        str
    ] = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
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
    runem_stdout: typing.List[
        str
    ] = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
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
    runem_stdout: typing.List[
        str
    ] = _run_full_config_runem(  # pylint: disable=no-value-for-parameter
        runem_cli_switches=runem_cli_switches
    )
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
