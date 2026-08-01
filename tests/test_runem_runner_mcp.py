from __future__ import annotations

import argparse
import json
import pathlib
import pickle
import sys
from collections import defaultdict
from datetime import timedelta

import pytest
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.mcp import runner as runem_runner_mcp
from runem.run_command import RunCommandBadExitCode
from runem.types.runem_config import JobConfig

# pylint: disable=protected-access


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


def test_get_run_ctx_returns_root_and_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runem_runner_mcp, "_load_metadata", _metadata)

    payload = yaml.safe_load(runem_runner_mcp.get_run_ctx())

    assert payload == {"run_ctx": {"config_file": ".runem.yml", "pwd": "."}}


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


def test_failure_payload_preserves_job_name_and_command_output() -> None:
    failure = RunCommandBadExitCode("compiler diagnostic")
    failure.job_name = "dummy:job:name"
    round_tripped = pickle.loads(pickle.dumps(failure))

    assert runem_runner_mcp._failed_job_names(round_tripped) == ["dummy:job:name"]
    assert runem_runner_mcp._failure_payload(round_tripped) == [
        {
            "job": "dummy:job:name",
            "message": "Bad exit-code",
            "output": "compiler diagnostic",
        }
    ]


def test_failed_job_is_not_also_reported_as_skipped() -> None:
    metadata = _metadata()
    assert (
        runem_runner_mcp._skipped_job_names(
            metadata,
            defaultdict(
                list,
                {"build": [metadata.jobs["build"][0]]},
            ),
            {"test"},
        )
        == []
    )


def test_imported_config_is_visible_to_mcp_tools(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- config:\n    phases: [analysis]\n- import: imported.yml\n")
    imported.write_text(
        "- job:\n"
        "    command: python -m pytest\n"
        "    label: imported test\n"
        "    when:\n"
        "      phase: analysis\n"
        "      tags: [py]\n"
    )

    sources = json.loads(runem_runner_mcp.list_config_sources(fmt="json"))
    jobs = json.loads(runem_runner_mcp.list_jobs(names_only=True, fmt="json"))
    dry_run = json.loads(
        runem_runner_mcp.execute(jobs=["imported test"], dry_run=True, fmt="json")
    )

    assert sources == {
        "imports": [
            {
                "from": str(root.resolve()),
                "requested_path": "imported.yml",
                "to": str(imported.resolve()),
            }
        ],
        "sources": [str(root.resolve()), str(imported.resolve())],
    }
    assert jobs == {"jobs": ["imported test"]}
    assert dry_run["status"] == "dry_run"
    assert dry_run["selected_jobs"] == ["imported test"]


def test_mcp_import_error_is_structured(tmp_path: pathlib.Path) -> None:
    root = tmp_path / ".runem.yml"
    root.write_text("- import: missing.yml\n")

    payload = json.loads(runem_runner_mcp.list_config_sources(fmt="json"))

    assert payload["error"] == {
        "code": "import_not_file",
        "import_chain": [str(root.resolve())],
        "message": (
            f"Unable to import 'missing.yml' from '{root.resolve()}': target does "
            f"not exist or is not a regular file; import chain: {root.resolve()}"
        ),
        "requested_path": "missing.yml",
        "source": str(root.resolve()),
    }


@pytest.fixture
def anyio_backend() -> str:
    """Use the transport implementation supported by the MCP standard-I/O client."""
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_server_transport_lists_imported_config(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / ".runem.yml"
    imported = tmp_path / "imported.yml"
    root.write_text("- config:\n    phases: [analysis]\n- import: imported.yml\n")
    imported.write_text(
        "- job:\n"
        "    command: python -m pytest\n"
        "    label: imported test\n"
        "    when:\n"
        "      phase: analysis\n"
    )
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "runem.mcp.runner"],
        cwd=tmp_path,
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            source_result = await session.call_tool("list_config_sources")
            jobs_result = await session.call_tool(
                "list_jobs", {"names_only": True, "fmt": "json"}
            )

    assert "list_config_sources" in [tool.name for tool in tools.tools]
    source_content = source_result.content[0]
    jobs_content = jobs_result.content[0]
    assert isinstance(source_content, TextContent)
    assert isinstance(jobs_content, TextContent)
    assert yaml.safe_load(source_content.text)["sources"] == [
        str(root.resolve()),
        str(imported.resolve()),
    ]
    assert json.loads(jobs_content.text) == {"jobs": ["imported test"]}
