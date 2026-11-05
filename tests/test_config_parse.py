import io
import pathlib
import typing
import unittest
from argparse import Namespace
from collections import defaultdict
from contextlib import redirect_stdout
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from runem.config.config_metadata import ConfigMetadata
from runem.config_parse import (
    _ConfigMetadataCollector,
    _parse_global_config,
    _parse_hook_config,
    _parse_job,
    _parse_job_config,
    load_config_metadata,
)
from runem.hook.hook_name import HookName
from runem.types.common import OrderedPhases
from runem.types.errors import FunctionNotFound, SystemExitBad
from runem.types.runem_config import (
    Config,
    GlobalConfig,
    GlobalSerialisedConfig,
    HookConfig,
    HookSerialisedConfig,
    JobConfig,
    JobSerialisedConfig,
    PhaseGroupedJobs,
)

# pylint: disable=protected-access


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
    metadata = ConfigMetadata(
        pathlib.Path(__file__), Namespace(verbose=False, silent=True)
    )
    metadata.all_job_tags = {"py"}
    collector = _ConfigMetadataCollector(metadata)
    _parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        config_collector=collector,
    )
    assert metadata.all_job_tags == {"format", "py"}
    assert metadata.jobs == {
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
    assert metadata.all_job_names == {"reformat py"}
    assert metadata.all_job_phases == {"edit"}


def test_parse_job_config_handles_multiple_cwd() -> None:
    """Tests that multiple cwd generate jobs per cwd."""
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_parse_job_config",
        },
        "ctx": {"cwd": ["path/a", "path/b"]},
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
    metadata = ConfigMetadata(pathlib.Path(__file__), Namespace(verbose=False))
    metadata.all_job_tags = {"py"}
    collector = _ConfigMetadataCollector(metadata)
    _parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        config_collector=collector,
    )
    assert metadata.all_job_tags == {"a", "b", "format", "py"}, (
        "tags should include the explicit"
    )
    assert metadata.jobs == {
        "edit": [
            {
                "addr": {
                    "file": "test_config_parse.py",
                    "function": "test_parse_job_config",
                },
                "ctx": {"cwd": "path/a"},
                "label": "reformat py(path/a)",
                "when": {"phase": "edit", "tags": set(("a", "py", "format"))},
            },
            {
                "addr": {
                    "file": "test_config_parse.py",
                    "function": "test_parse_job_config",
                },
                "ctx": {"cwd": "path/b"},
                "label": "reformat py(path/b)",
                "when": {"phase": "edit", "tags": set(("b", "py", "format"))},
            },
        ]
    }
    assert metadata.all_job_names == {"reformat py(path/a)", "reformat py(path/b)"}
    assert metadata.all_job_phases == {"edit"}


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
    metadata = ConfigMetadata(pathlib.Path(__file__), Namespace(verbose=False))
    metadata.all_job_tags = {"py"}
    collector = _ConfigMetadataCollector(metadata)

    # first call should be fine
    _parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        config_collector=collector,
    )
    assert job_config["label"] in metadata.all_job_names

    # second call should error
    with pytest.raises(SystemExit):
        _parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            config_collector=collector,
        )


def test_parse_job_config_throws_on_missing_key() -> None:
    """Tests for expected keys are reported if missing."""
    job_config: JobConfig = {
        "addr": {  # type: ignore[typeddict-item]
            "file": __file__,
            # intentionally removed:
            # "function": "test_parse_job_config",
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
    metadata = ConfigMetadata(pathlib.Path(__file__), Namespace(verbose=False))
    metadata.all_job_tags = {"py"}
    collector = _ConfigMetadataCollector(metadata)
    with pytest.raises(ValueError) as err_info:
        _parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            config_collector=collector,
        )
    assert str(err_info.value).startswith(
        ("job config entry is missing 'function' data")
    )


def test_parse_global_config_empty() -> None:
    """Test the global config parse handles empty data."""
    dummy_global_config: GlobalConfig = {
        "phases": tuple(),
        "min_version": None,
        "options": [],
        "files": [],
    }
    metadata = ConfigMetadata(pathlib.Path(__file__), Namespace(verbose=False))
    collector = _ConfigMetadataCollector(metadata)
    _parse_global_config(dummy_global_config, collector)
    assert metadata.phases == tuple()
    assert metadata.options_config == tuple()
    assert not metadata.file_filters


def test_parse_global_config_missing() -> None:
    """Test the global config parse handles missing data."""
    dummy_global_config: GlobalConfig = {  # type: ignore
        "phases": tuple(),
        # intentionally missing: "options": [],
        # intentionally missing: "files": [],
    }
    metadata = ConfigMetadata(pathlib.Path(__file__), Namespace(verbose=False))
    collector = _ConfigMetadataCollector(metadata)
    _parse_global_config(dummy_global_config, collector)
    assert metadata.phases == tuple()
    assert metadata.options_config == tuple()
    assert not metadata.file_filters


def test_parse_global_config_full() -> None:
    """Test the global config parse handles populated data."""
    dummy_global_config: GlobalConfig = {
        "phases": ("edit", "test"),
        "min_version": None,
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
    metadata = ConfigMetadata(
        pathlib.Path(__file__), Namespace(verbose=False, silent=False)
    )
    collector = _ConfigMetadataCollector(metadata)
    _parse_global_config(dummy_global_config, collector)
    assert metadata.phases == ("edit", "test")
    assert metadata.options_config == (
        {
            "name": "dummy option",
            "aliases": None,
            "default": False,
            "type": "bool",
            "desc": "dummy description",
        },
    )
    assert metadata.file_filters == {"dummy tag": {"regex": ".*", "tag": "dummy tag"}}


@pytest.mark.parametrize(
    "do_hooks",
    [
        True,
        False,
    ],
)
def test_load_config_metadata(do_hooks: bool) -> None:
    """Test parsing works for a full config."""
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1",),
            "files": [],
            "min_version": None,
            "options": [],
        }
    }
    job_config: JobSerialisedConfig = {
        "job": {
            "addr": {
                "file": __file__,
                "function": "test_load_config_metadata",
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
    if do_hooks:
        # optionally do hooks, to capture verbose logging without having to
        # write another test.
        hook_config: HookSerialisedConfig = {
            "hook": {
                "command": "echo 'test hook command'",
                "hook_name": HookName("on-exit"),
            }
        }
        full_config.append(hook_config)

    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    expected_job: JobConfig = {
        "addr": {
            "file": "test_config_parse.py",
            "function": "test_load_config_metadata",
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
    expected_config_metadata = ConfigMetadata(
        config_file_path, Namespace(verbose=False, silent=False)
    )
    expected_config_metadata.phases = ("dummy phase 1",)
    expected_config_metadata.jobs = expected_jobs
    expected_config_metadata.all_job_names = {"dummy job label"}
    expected_config_metadata.all_job_phases = {"dummy phase 1"}
    expected_config_metadata.all_job_tags = {"dummy tag 1", "dummy tag 2"}

    with io.StringIO() as buf, redirect_stdout(buf):
        result: ConfigMetadata = load_config_metadata(
            full_config, config_file_path, [], Namespace(verbose=False, silent=False)
        )
        stdout = buf.getvalue().split("\n")
    assert stdout == [""]
    assert result.phases == expected_config_metadata.phases
    assert result.options_config == expected_config_metadata.options_config
    assert result.file_filters == expected_config_metadata.file_filters
    assert result.jobs == expected_config_metadata.jobs
    assert result.all_job_names == expected_config_metadata.all_job_names
    assert result.all_job_phases == expected_config_metadata.all_job_phases
    assert result.all_job_tags == expected_config_metadata.all_job_tags


def test_load_config_metadata_hooks() -> None:
    """Test parsing works for a full config, with user hook."""
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1",),
            "files": [],
            "min_version": None,
            "options": [],
        }
    }
    job_config: JobSerialisedConfig = {
        "job": {
            "addr": {
                "file": __file__,
                "function": "test_load_config_metadata",
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
    hook_config: HookSerialisedConfig = {
        "hook": {
            "command": "echo 'test hook command'",
            "hook_name": HookName("on-exit"),
        }
    }
    user_hook_config_1: HookSerialisedConfig = {
        "hook": {
            "command": "echo 'test user-hook command 1'",
            "hook_name": HookName("on-exit"),
        }
    }
    user_hook_config_2: HookSerialisedConfig = {
        "hook": {
            "command": "echo 'test user-hook command 2'",
            "hook_name": HookName("on-exit"),
        }
    }
    user_jobs_only_config: JobSerialisedConfig = {
        "job": {
            "command": "echo 'user job'",
            "label": "user job",
        }
    }
    full_config: Config = [global_config, job_config, hook_config]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"
    expected_job: JobConfig = {
        "addr": {
            "file": "test_config_parse.py",
            "function": "test_load_config_metadata",
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
    # User jobs are collected before the project defines its phase order.
    expected_jobs["<NO PHASES FOUND>"] = [user_jobs_only_config["job"]]
    expected_config_metadata = ConfigMetadata(
        config_file_path, Namespace(verbose=False)
    )
    expected_config_metadata.phases = ("dummy phase 1",)
    expected_config_metadata.jobs = expected_jobs
    expected_config_metadata.all_job_names = {"dummy job label", "user job"}
    expected_config_metadata.all_job_phases = {"dummy phase 1", "<NO PHASES FOUND>"}
    expected_config_metadata.all_job_tags = {"dummy tag 1", "dummy tag 2"}

    user_config_1: Config = [
        user_hook_config_1,
    ]
    user_config_2: Config = [
        user_hook_config_2,
    ]
    user_config_jobs_only: Config = [
        user_jobs_only_config,
    ]

    result: ConfigMetadata = load_config_metadata(
        full_config,
        config_file_path,
        [
            (user_config_1, pathlib.Path(__file__)),
            (user_config_2, pathlib.Path(__file__)),
            (user_config_jobs_only, pathlib.Path(__file__)),
        ],
        Namespace(verbose=False, silent=False),
    )
    assert result.hook_manager._hooks_store == {
        HookName.ON_EXIT: [
            user_hook_config_1["hook"],
            user_hook_config_2["hook"],
            hook_config["hook"],
        ]
    }
    assert result.phases == expected_config_metadata.phases
    assert result.options_config == expected_config_metadata.options_config
    assert result.file_filters == expected_config_metadata.file_filters
    assert result.jobs == expected_config_metadata.jobs
    assert result.all_job_names == expected_config_metadata.all_job_names
    assert result.all_job_phases == expected_config_metadata.all_job_phases
    assert result.all_job_tags == expected_config_metadata.all_job_tags


def test_load_config_metadata_raises_on_invalid() -> None:
    """Test throws for an invalid config."""
    invalid_config_spec: GlobalSerialisedConfig = {  # type: ignore
        "invalid": None,
    }
    invalid_config: Config = [
        invalid_config_spec,
    ]
    config_file_path = pathlib.Path(__file__).parent / ".runem.yml"

    with pytest.raises(RuntimeError):
        load_config_metadata(
            invalid_config,
            config_file_path,
            [],
            Namespace(verbose=False, silent=False, jobs=[]),
        )


def test_load_config_metadata_duplicated_global_raises() -> None:
    """Test the global config parse raises with duplicated global config."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("dummy phase 1",),
            "min_version": None,
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
        load_config_metadata(
            invalid_config, config_file_path, [], Namespace(verbose=False, silent=False)
        )


def test_load_config_metadata_empty_phases_raises() -> None:
    """Test the global config raises if the phases are empty."""
    dummy_global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": (),
            "min_version": None,
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
        load_config_metadata(
            invalid_config, config_file_path, [], Namespace(verbose=False, silent=False)
        )


def test_load_config_metadata_missing_phases_raises() -> None:
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
        load_config_metadata(
            invalid_config,
            config_file_path,
            [],
            Namespace(
                verbose=False,
                silent=False,
                jobs=[],
            ),
        )


@patch(
    "runem.config_parse._parse_global_config",
    return_value=None,
)
def test_load_config_metadata_warning_if_missing_phase_order(
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
        load_config_metadata(
            valid_config, config_file_path, [], Namespace(verbose=False, silent=False)
        )
        run_command_stdout = buf.getvalue()

    assert run_command_stdout.split("\n") == [
        "runem: WARNING: phase ordering not configured! Runs will be non-deterministic!",
        "",
    ]
    mock_parse_global_config.assert_called()


@patch(
    "runem.config_parse.get_job_wrapper",
    return_value=None,
)
def test_parse_job_with_tags(mock_get_job_wrapper: Mock) -> None:
    """Test case where job_tags is not empty."""
    cfg_filepath = pathlib.Path(__file__)
    job_config: JobConfig = {
        "label": "Job1",
        "when": {
            "tags": {
                "tag1",
                "tag2",
            }
        },
    }
    metadata = ConfigMetadata(cfg_filepath, Namespace(verbose=False, silent=True))
    metadata.phases = ("phase1", "phase2")
    collector = _ConfigMetadataCollector(metadata)

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            collector,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [
        "runem: WARNING: no phase found for 'Job1', using 'phase1'",
        "",
    ]
    assert metadata.all_job_tags == {"tag1", "tag2"}


@patch(
    "runem.config_parse.get_job_wrapper",
    return_value=None,
)
def test_parse_job_without_tags(mock_get_job_wrapper: Mock) -> None:
    """Test case where job_tags is empty or None."""
    cfg_filepath = pathlib.Path(__file__)
    job_config: JobConfig = {
        "label": "Job2",
        "when": {
            "phase": "phase1",
        },
    }
    metadata = ConfigMetadata(cfg_filepath, Namespace(verbose=False, silent=True))
    metadata.phases = ("phase1", "phase2")
    collector = _ConfigMetadataCollector(metadata)

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            collector,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [""]
    assert not metadata.all_job_tags


@patch(
    "runem.config_parse.get_job_wrapper",
    side_effect=FunctionNotFound("a test message"),
)
def test_parse_job_with_bad_function(mock_get_job_wrapper: Mock) -> None:
    """Test case where job_tags is empty or None."""
    cfg_filepath = pathlib.Path(__file__)
    job_config: JobConfig = {
        "label": "Job2",
        "when": {
            "phase": "phase1",
        },
    }
    metadata = ConfigMetadata(cfg_filepath, Namespace(verbose=False, silent=True))
    metadata.phases = ("phase1", "phase2")
    collector = _ConfigMetadataCollector(metadata)

    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(SystemExitBad):
            _parse_job(
                cfg_filepath,
                job_config,
                collector,
            )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [
        "runem: ERROR: Whilst loading job 'Job2'. a test message",
        "",
    ]
    assert not metadata.all_job_tags


@pytest.mark.parametrize(
    "phase_order",
    [
        ("phase1", "phase2"),
        (),
    ],
)
@patch(
    "runem.config_parse.get_job_wrapper",
    return_value=None,
)
def test_parse_job_with_missing_phase(
    mock_get_job_wrapper: Mock,
    phase_order: OrderedPhases,
) -> None:
    """Test case where job_tags is empty or None."""
    cfg_filepath = pathlib.Path(__file__)
    job_config: JobConfig = {
        "label": "Job2",
        "when": {
            # "phase": "phase1",
        },
    }
    metadata = ConfigMetadata(cfg_filepath, Namespace(verbose=False, silent=True))
    metadata.phases = phase_order
    collector = _ConfigMetadataCollector(metadata)

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            collector,
            warn_missing_phase=False,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [""]
    assert not metadata.all_job_tags
    expected_phase = "<NO PHASES FOUND>"
    if phase_order:
        expected_phase = phase_order[0]
    assert metadata.jobs == {expected_phase: [job_config]}
    assert metadata.all_job_names == {"Job2"}
    assert metadata.all_job_phases == {expected_phase}


def test_parse_hook_config_with_valid_config() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        "hook_name": HookName("on-exit"),
    }
    # should execute without raising
    _parse_hook_config(
        hook,
        cfg_filepath,
        mock.MagicMock(),
        verbose=False,
    )


def test_parse_hook_config_with_in_valid_hook_name() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        "hook_name": "bad-hook-name",  # type: ignore
    }
    with pytest.raises(ValueError):
        _parse_hook_config(
            hook,
            cfg_filepath,
            mock.MagicMock(),
            verbose=False,
        )


def test_parse_hook_config_with_missing_hook_name() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        # "hook_name": HookName("on-exit"),
    }
    with pytest.raises(ValueError):
        _parse_hook_config(
            hook,
            cfg_filepath,
            mock.MagicMock(),
            verbose=False,
        )


def test_parse_hook_config_with_missing_command() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        # "command": "echo 'test hook command'",
        "hook_name": HookName("on-exit"),
    }
    with pytest.raises(ValueError):
        _parse_hook_config(
            hook,
            cfg_filepath,
            mock.MagicMock(),
            verbose=False,
        )


def test_parse_hook_config_with_bad_function_address() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        # "command": "echo 'test hook command'",
        "addr": {
            "file": __file__,
            "function": "non_existent_function",
        },
        "hook_name": HookName("on-exit"),
    }
    with pytest.raises(SystemExitBad):
        _parse_hook_config(
            hook,
            cfg_filepath,
            mock.MagicMock(),
            verbose=False,
        )


@pytest.mark.parametrize(
    "hook_type",
    [
        "non-existent-hook",
        123,
    ],
)
def test_parse_hook_config_with_bad_hook_name_types(hook_type: typing.Any) -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        "hook_name": hook_type,
    }
    with pytest.raises(ValueError):
        _parse_hook_config(
            hook,
            cfg_filepath,
            mock.MagicMock(),
            verbose=False,
        )
