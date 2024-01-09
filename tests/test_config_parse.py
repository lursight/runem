import io
import pathlib
import unittest
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.config_parse import _parse_global_config, parse_config, parse_job_config
from runem.types import (
    Config,
    GlobalConfig,
    GlobalSerialisedConfig,
    JobConfig,
    JobNames,
    JobPhases,
    JobSerialisedConfig,
    JobTags,
    PhaseGroupedJobs,
)


def test_parse_job_config() -> None:
    """Tests basic parsing of the job config."""
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
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    phases: JobPhases = set()
    parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        in_out_tags=tags,
        in_out_jobs_by_phase=jobs_by_phase,
        in_out_job_names=job_names,
        in_out_phases=phases,
    )
    assert tags == {"format", "py"}
    assert jobs_by_phase == {
        "edit": [
            {
                "addr": {
                    "file": "test_config_parse.py",
                    "function": "test_parse_job_config",
                },
                "label": "reformat py",
                "when": {"phase": "edit", "tags": set(("py", "format"))},
            }
        ]
    }
    assert job_names == {"reformat py"}
    assert phases == {"edit"}


def test_parse_job_config_throws_on_dupe_name() -> None:
    """Tests for job-name clashes."""
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
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set(("reformat py",))
    phases: JobPhases = set()
    with pytest.raises(SystemExit):
        parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=phases,
        )


def test_parse_job_config_throws_on_missing_key() -> None:
    """Tests for expected keys are reported if missing."""
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_job_config",
        },
        # intentionally removed:
        # "label": "reformat py",
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
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set(("reformat py",))
    phases: JobPhases = set()
    with pytest.raises(ValueError):
        parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=phases,
        )


def test_parse_global_config_empty() -> None:
    """Test the global config parse handles empty data."""
    dummy_global_config: GlobalConfig = {
        "phases": tuple(),
        "options": [],
        "files": [],
    }
    phases, options, file_filters = _parse_global_config(dummy_global_config)
    assert phases == tuple()
    assert options == tuple()
    assert not file_filters


def test_parse_global_config_missing() -> None:
    """Test the global config parse handles missing data."""
    dummy_global_config: GlobalConfig = {  # type: ignore
        "phases": tuple(),
        # intentionally missing: "options": [],
        # intentionally missing: "files": [],
    }
    phases, options, file_filters = _parse_global_config(dummy_global_config)
    assert phases == tuple()
    assert options == tuple()
    assert not file_filters


def test_parse_global_config_full() -> None:
    """Test the global config parse handles missing data."""
    dummy_global_config: GlobalConfig = {
        "phases": tuple(),
        "options": [
            {
                "option": {
                    "name": "dummy option",
                    "aliases": None,
                    "default": False,
                    "type": "bool",
                    "desc": "dummy description",
                }
            }
        ],
        "files": [{"filter": {"tag": "dummy tag", "regex": ".*"}}],
    }
    phases, options, file_filters = _parse_global_config(dummy_global_config)
    assert phases == tuple()
    assert options == (
        {
            "name": "dummy option",
            "aliases": None,
            "default": False,
            "type": "bool",
            "desc": "dummy description",
        },
    )
    assert file_filters == {"dummy tag": {"regex": ".*", "tag": "dummy tag"}}


def test_parse_config() -> None:
    """Test parsing works for a full config."""
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1",),
            "files": [],
            "options": [],
        }
    }
    job_config: JobSerialisedConfig = {
        "job": {
            "addr": {
                "file": __file__,
                "function": "test_parse_config",
            },
            "label": "dummy job label",
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
    full_config: Config = [global_config, job_config]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    expected_job: JobConfig = {
        "addr": {
            "file": "test_config_parse.py",
            "function": "test_parse_config",
        },
        "label": "dummy job label",
        "when": {
            "phase": "dummy phase 1",
            "tags": {"dummy tag 1", "dummy tag 2"},
        },
    }
    expected_jobs: PhaseGroupedJobs = defaultdict(list)
    expected_jobs["dummy phase 1"] = [
        expected_job,
    ]
    expected_config_metadata: ConfigMetadata = ConfigMetadata(
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

    result: ConfigMetadata = parse_config(full_config, config_file_path)
    assert result.phases == expected_config_metadata.phases
    assert result.options_config == expected_config_metadata.options_config
    assert result.file_filters == expected_config_metadata.file_filters
    assert result.jobs == expected_config_metadata.jobs
    assert result.all_job_names == expected_config_metadata.all_job_names
    assert result.all_job_phases == expected_config_metadata.all_job_phases
    assert result.all_job_tags == expected_config_metadata.all_job_tags


def test_parse_config_raises_on_invalid() -> None:
    """Test throws for an invalid config."""
    invalid_config_spec: GlobalSerialisedConfig = {  # type: ignore
        "invalid": None,
    }
    invalid_config: Config = [
        invalid_config_spec,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    with pytest.raises(RuntimeError):
        parse_config(invalid_config, config_file_path)


def test_parse_config_duplicated_global_raises() -> None:
    """Test the global config parse raises with duplicated global config."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1",),
            "options": [
                {
                    "option": {
                        "name": "dummy option",
                        "aliases": None,
                        "default": False,
                        "type": "bool",
                        "desc": "dummy description",
                    }
                }
            ],
            "files": [{"filter": {"tag": "dummy tag", "regex": ".*"}}],
        }
    }
    invalid_config: Config = [
        dummy_global_config,
        dummy_global_config,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    with pytest.raises(ValueError):
        parse_config(invalid_config, config_file_path)


def test_parse_config_empty_phases_raises() -> None:
    """Test the global config raises if the phases are empty."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": (),
            "options": [
                {
                    "option": {
                        "name": "dummy option",
                        "aliases": None,
                        "default": False,
                        "type": "bool",
                        "desc": "dummy description",
                    }
                }
            ],
            "files": [{"filter": {"tag": "dummy tag", "regex": ".*"}}],
        }
    }
    invalid_config: Config = [
        dummy_global_config,
        dummy_global_config,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    with pytest.raises(ValueError):
        parse_config(invalid_config, config_file_path)


def test_parse_config_missing_phases_raises() -> None:
    """Test the global config raises if the phases are missing."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {  # type: ignore
            "options": [
                {
                    "option": {
                        "name": "dummy option",
                        "aliases": None,
                        "default": False,
                        "type": "bool",
                        "desc": "dummy description",
                    }
                }
            ],
            "files": [{"filter": {"tag": "dummy tag", "regex": ".*"}}],
        }
    }
    invalid_config: Config = [
        dummy_global_config,
        dummy_global_config,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    with pytest.raises(ValueError):
        parse_config(invalid_config, config_file_path)


@patch(
    "runem.config_parse._parse_global_config",
    return_value=(None, (), {}),
)
def test_parse_config_warning_if_missing_phase_order(
    mock_parse_global_config: unittest.mock.Mock,
) -> None:
    """Test the global config raises if the phases are missing."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {  # type: ignore
            "options": [
                {
                    "option": {
                        "name": "dummy option",
                        "aliases": None,
                        "default": False,
                        "type": "bool",
                        "desc": "dummy description",
                    }
                }
            ],
            "files": [{"filter": {"tag": "dummy tag", "regex": ".*"}}],
        }
    }
    valid_config: Config = [
        dummy_global_config,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    # run the command and capture output
    with io.StringIO() as buf, redirect_stdout(buf):
        parse_config(valid_config, config_file_path)
        run_command_stdout = buf.getvalue()

    assert run_command_stdout.split("\n") == [
        "runem: WARNING: phase ordering not configured! Runs will be non-deterministic!",
        "",
    ]
    mock_parse_global_config.assert_called()
