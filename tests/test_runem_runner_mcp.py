from __future__ import annotations

import argparse
import pathlib
from collections import defaultdict
from datetime import timedelta

import pytest
import yaml

import runem_runner_mcp
from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.types.runem_config import JobConfig


def _metadata() -> ConfigMetadata:
    jobs = defaultdict(list)
    build_job: JobConfig = {
        "label": "build",
        "command": "python -m build",
        "when": {"phase": "build", "tags": {"py", "package"}},
    }
    test_job: JobConfig = {
        "label": "test",
        "module": "tests.example.test",
        "ctx": {"cwd": "src"},
        "when": {"phase": "test", "tags": {"py"}},
    }
    jobs["build"].append(build_job)
    jobs["test"].append(test_job)
    metadata = ConfigMetadata(
        cfg_filepath=pathlib.Path(".runem.yml"),
        phases=("build", "test"),
        options_config=(
            {
                "name": "coverage",
                "default": True,
                "type": "bool",
                "desc": "collect coverage",
            },
        ),
        file_filters={
            "py": {"tag": "py", "regex": ".*\\.py"},
            "package": {"tag": "package", "regex": "pyproject\\.toml"},
        },
        hook_manager=None,  # type: ignore[arg-type]
        jobs=jobs,
        all_job_names={"build", "test"},
        all_job_phases={"build", "test"},
        all_job_tags={"package", "py"},
    )
    metadata.set_cli_data(
        args=argparse.Namespace(verbose=False, procs=1),
        jobs_to_run={"build", "test"},
        phases_to_run={"build", "test"},
        tags_to_run={"package", "py"},
        tags_to_avoid=set(),
        options=InformativeDict({"coverage": True}),
    )
    return metadata


def test_list_jobs_is_minimal_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runem_runner_mcp, "_load_metadata", _metadata)

    payload = yaml.safe_load(runem_runner_mcp.list_jobs())

    assert payload == {"jobs": [{"name": "build"}, {"name": "test"}]}


def test_list_jobs_can_include_compact_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runem_runner_mcp, "_load_metadata", _metadata)

    payload = yaml.safe_load(runem_runner_mcp.list_jobs(include_docs=True))

    assert payload["jobs"][0] == {
        "command": "python -m build",
        "description": "build",
        "name": "build",
        "phase": "build",
        "tags": ["package", "py"],
    }
    assert payload["jobs"][1]["ctx"] == {"cwd": "src"}
    assert payload["jobs"][1]["module"] == "tests.example.test"


def test_list_options_defaults_to_name_default_and_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runem_runner_mcp, "_load_metadata", _metadata)

    payload = yaml.safe_load(runem_runner_mcp.list_options())

    assert payload == {
        "options": [{"default": True, "name": "coverage", "type": "bool"}]
    }


def test_minimal_identifier_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runem_runner_mcp, "_load_metadata", _metadata)

    assert yaml.safe_load(runem_runner_mcp.list_phases()) == {
        "phases": ["build", "test"]
    }
    assert yaml.safe_load(runem_runner_mcp.list_tags()) == {"tags": ["package", "py"]}
    assert yaml.safe_load(runem_runner_mcp.list_filters()) == {
        "filters": ["package", "py"]
    }


def test_get_timing_filters_latest_run_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runem_runner_mcp,
        "LATEST_RUN_METADATA",
        {
            "test": [
                (
                    {
                        "job": ("test", timedelta(seconds=2)),
                        "commands": [("pytest", timedelta(seconds=1))],
                    },
                    None,
                )
            ]
        },
    )

    payload = yaml.safe_load(runem_runner_mcp.get_timing(job="test", sub_job="pytest"))

    assert payload == {
        "timing": [
            {
                "commands": [
                    {"duration": 1.0, "status": "recorded", "sub_job": "pytest"}
                ],
                "duration": 2.0,
                "job": "test",
                "phase": "test",
                "status": "recorded",
            }
        ]
    }
