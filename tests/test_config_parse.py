import io
import pathlib
import typing
import unittest
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import MagicMock, Mock, patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.config_parse import (
    _parse_global_config,
    _parse_job,
    load_config_metadata,
    parse_hook_config,
    parse_job_config,
)
from runem.types.common import JobNames, JobPhases, JobTags, OrderedPhases
from runem.types.errors import FunctionNotFound
from runem.types.hooks import HookName
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
    phase_order: OrderedPhases = ()
    parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        in_out_tags=tags,
        in_out_jobs_by_phase=jobs_by_phase,
        in_out_job_names=job_names,
        in_out_phases=phases,
        phase_order=phase_order,
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
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    phases: JobPhases = set()
    phase_order: OrderedPhases = ()
    parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        in_out_tags=tags,
        in_out_jobs_by_phase=jobs_by_phase,
        in_out_job_names=job_names,
        in_out_phases=phases,
        phase_order=phase_order,
    )
    assert tags == {"a", "b", "format", "py"}, "tags should include the explicit"
    assert jobs_by_phase == {
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
    assert job_names == {"reformat py(path/a)", "reformat py(path/b)"}
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
    job_names: JobNames = set()
    phases: JobPhases = set()
    phase_order: OrderedPhases = ()

    # first call should be fine
    parse_job_config(
        cfg_filepath=pathlib.Path(__file__),
        job=job_config,
        in_out_tags=tags,
        in_out_jobs_by_phase=jobs_by_phase,
        in_out_job_names=job_names,
        in_out_phases=phases,
        phase_order=phase_order,
    )
    assert job_config["label"] in job_names

    # second call should error
    with pytest.raises(SystemExit):
        parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=phases,
            phase_order=phase_order,
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
    tags: JobTags = set(["py"])
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    phases: JobPhases = set()
    phase_order: OrderedPhases = ()
    with pytest.raises(ValueError) as err_info:
        parse_job_config(
            cfg_filepath=pathlib.Path(__file__),
            job=job_config,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=phases,
            phase_order=phase_order,
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

    with io.StringIO() as buf, redirect_stdout(buf):
        result: ConfigMetadata = load_config_metadata(full_config, config_file_path, [])
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
            "command": "echo 'should not be seen'",
            "label": "SHOULD NOT SEE ME",
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
    )
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
        load_config_metadata(invalid_config, config_file_path, [])


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
        load_config_metadata(invalid_config, config_file_path, [])


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
        load_config_metadata(invalid_config, config_file_path, [])


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
        load_config_metadata(invalid_config, config_file_path, [])


@patch(
    "runem.config_parse._parse_global_config",
    return_value=(None, (), {}),
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
        load_config_metadata(valid_config, config_file_path, [])
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
    in_out_tags: JobTags = set()
    in_out_jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    in_out_job_names: JobNames = set()
    in_out_phases: JobPhases = set()
    phase_order: OrderedPhases = ("phase1", "phase2")

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            in_out_tags,
            in_out_jobs_by_phase,
            in_out_job_names,
            in_out_phases,
            phase_order,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [
        "runem: WARNING: no phase found for 'Job1', using 'phase1'",
        "",
    ]
    assert in_out_tags == {"tag1", "tag2"}


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
    in_out_tags: JobTags = set()
    in_out_jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    in_out_job_names: JobNames = set()
    in_out_phases: JobPhases = set()
    phase_order: OrderedPhases = ("phase1", "phase2")

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            in_out_tags,
            in_out_jobs_by_phase,
            in_out_job_names,
            in_out_phases,
            phase_order,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [""]
    assert not in_out_tags


@patch(
    "runem.config_parse.get_job_wrapper",
    side_effect=FunctionNotFound,
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
    in_out_tags: JobTags = set()
    in_out_jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    in_out_job_names: JobNames = set()
    in_out_phases: JobPhases = set()
    phase_order: OrderedPhases = ("phase1", "phase2")

    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(FunctionNotFound):
            _parse_job(
                cfg_filepath,
                job_config,
                in_out_tags,
                in_out_jobs_by_phase,
                in_out_job_names,
                in_out_phases,
                phase_order,
            )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [""]
    assert not in_out_tags


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
    in_out_tags: JobTags = set()
    in_out_jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    in_out_job_names: JobNames = set()
    in_out_phases: JobPhases = set()

    with io.StringIO() as buf, redirect_stdout(buf):
        _parse_job(
            cfg_filepath,
            job_config,
            in_out_tags,
            in_out_jobs_by_phase,
            in_out_job_names,
            in_out_phases,
            phase_order,
            warn_missing_phase=False,
        )
        run_command_stdout = buf.getvalue().split("\n")

    mock_get_job_wrapper.assert_called_once()

    assert run_command_stdout == [""]
    assert not in_out_tags


def test_parse_hook_config_with_valid_config() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        "hook_name": HookName("on-exit"),
    }
    # should execute without raising
    parse_hook_config(hook, cfg_filepath)


def test_parse_hook_config_with_in_valid_hook_name() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        "hook_name": "bad-hook-name",  # type: ignore
    }
    with pytest.raises(ValueError):
        parse_hook_config(hook, cfg_filepath)


def test_parse_hook_config_with_missing_hook_name() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        "command": "echo 'test hook command'",
        # "hook_name": HookName("on-exit"),
    }
    with pytest.raises(ValueError):
        parse_hook_config(hook, cfg_filepath)


def test_parse_hook_config_with_missing_command() -> None:
    cfg_filepath = pathlib.Path(__file__)
    hook: HookConfig = {
        # "command": "echo 'test hook command'",
        "hook_name": HookName("on-exit"),
    }
    with pytest.raises(ValueError):
        parse_hook_config(hook, cfg_filepath)


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
    with pytest.raises(FunctionNotFound):
        parse_hook_config(hook, cfg_filepath)


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
        parse_hook_config(hook, cfg_filepath)
