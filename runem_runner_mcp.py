"""Agentic MCP server wrapper for inspecting and running runem.

The module intentionally reuses runem's config loading, CLI parsing, filtering,
and execution internals.  It does not write or mutate config files.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import typing
from collections import defaultdict
from datetime import timedelta

import yaml
from typing_extensions import Literal

from runem.command_line import parse_args
from runem.config import load_project_config, load_user_configs
from runem.config_metadata import ConfigMetadata
from runem.config_parse import load_config_metadata
from runem.job import Job
from runem.job_filter import filter_jobs
from runem.runem import _main
from runem.types.common import PhaseName
from runem.types.runem_config import JobConfig, PhaseGroupedJobs
from runem.types.types_jobs import JobRunMetadatasByPhase, JobTiming

Format = Literal["yaml", "json"]
JsonLike = typing.Union[
    None,
    bool,
    int,
    float,
    str,
    typing.List["JsonLike"],
    typing.Dict[str, "JsonLike"],
]

MAX_CAPTURE_CHARS = 4000
LATEST_RUN_METADATA: typing.Optional[JobRunMetadatasByPhase] = None


class RunemMcpError(RuntimeError):
    """Structured error for MCP tool responses."""

    def __init__(self, code: str, message: str, hint: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint

    def as_payload(self) -> typing.Dict[str, typing.Dict[str, str]]:
        """Return a compact serialisable error payload."""
        return {
            "error": {"code": self.code, "message": self.message, "hint": self.hint}
        }


def _normalise(value: typing.Any) -> JsonLike:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, set):
        return [_normalise(item) for item in sorted(value)]
    if isinstance(value, tuple):
        return [_normalise(item) for item in value]
    if isinstance(value, list):
        return [_normalise(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _normalise(value[key]) for key in sorted(value.keys(), key=str)
        }
    return typing.cast(JsonLike, value)


def _serialise(payload: typing.Any, output_format: Format) -> str:
    normalised = _normalise(payload)
    if output_format == "json":
        return json.dumps(normalised, indent=2, sort_keys=True)
    return yaml.safe_dump(normalised, sort_keys=True)


def _with_error_handling(
    func: typing.Callable[[], typing.Any], output_format: Format
) -> str:
    try:
        return _serialise(func(), output_format)
    except RunemMcpError as err:
        return _serialise(err.as_payload(), output_format)
    except SystemExit as err:
        return _serialise(
            {
                "error": {
                    "code": "runem_system_exit",
                    "message": "runem exited while processing the request.",
                    "hint": "Validate the active .runem.yml and requested filters.",
                    "exit_code": err.code,
                }
            },
            output_format,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        return _serialise(
            {
                "error": {
                    "code": err.__class__.__name__,
                    "message": str(err),
                    "hint": "Inspect the active runem config and retry with narrower inputs.",
                }
            },
            output_format,
        )


def _load_metadata() -> ConfigMetadata:
    """Load and validate the active runem config using runem's discovery logic."""
    try:
        config, cfg_filepath = load_project_config()
    except SystemExit as err:
        raise RunemMcpError(
            "config_not_found",
            "Could not find .runem.yml from the current working directory.",
            "Run this MCP server from a runem project root.",
        ) from err

    user_configs = load_user_configs()
    return load_config_metadata(config, cfg_filepath, user_configs, silent=True)


def _job_name(job: JobConfig) -> str:
    return Job.get_job_name(job)


def _all_jobs(metadata: ConfigMetadata) -> typing.List[JobConfig]:
    jobs: typing.List[JobConfig] = []
    phase: PhaseName
    for phase in metadata.phases:
        jobs.extend(metadata.jobs[phase])
    return sorted(jobs, key=_job_name)


def _compact_job(job: JobConfig, include_docs: bool) -> typing.Dict[str, JsonLike]:
    data: typing.Dict[str, JsonLike] = {"name": _job_name(job)}
    when = job.get("when", {})
    if "tags" in when:
        data["tags"] = sorted(when["tags"])
    if "phase" in when:
        data["phase"] = when["phase"]
    if "ctx" in job and job["ctx"] is not None:
        data["ctx"] = typing.cast(JsonLike, job["ctx"])
    if include_docs:
        if "label" in job:
            data["description"] = job["label"]
        if "command" in job:
            data["command"] = job["command"]
        if "module" in job:
            data["module"] = job["module"]
        if "addr" in job:
            data["function"] = typing.cast(JsonLike, job["addr"])
    return data


def _filter_jobs_for_selection(
    metadata: ConfigMetadata,
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
) -> PhaseGroupedJobs:
    argv = _build_argv(jobs, tags, phases, None, dry_run=True)
    parsed = parse_args(metadata, argv)
    return filter_jobs(parsed)


def _validate_requested(
    metadata: ConfigMetadata,
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
    options: typing.Optional[typing.Dict[str, object]],
) -> None:
    _validate_names("job", jobs, metadata.all_job_names)
    _validate_names("tag", tags, metadata.all_job_tags)
    _validate_names("phase", phases, metadata.all_job_phases)
    option_names = {option["name"] for option in metadata.options_config}
    _validate_names("option", list(options or {}), option_names)


def _validate_names(
    kind: str, requested: typing.Optional[typing.List[str]], available: typing.Set[str]
) -> None:
    invalid = sorted(set(requested or []) - available)
    if invalid:
        raise RunemMcpError(
            "invalid_%s" % kind,
            "Unknown %s value(s): %s" % (kind, ", ".join(invalid)),
            "Choose from: %s" % ", ".join(sorted(available)),
        )


def list_jobs(
    include_docs: bool = False,
    names_only: bool = False,
    include_tags: bool = False,
    include_ctx: bool = False,
    include_phase: bool = False,
    format: Format = "yaml",
) -> str:
    """List jobs from the active runem config."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        if names_only:
            return {"jobs": [_job_name(job) for job in _all_jobs(metadata)]}
        jobs_payload = []
        for job in _all_jobs(metadata):
            if include_docs:
                data = _compact_job(job, include_docs=True)
            else:
                data = {"name": _job_name(job)}
                when = job.get("when", {})
                if include_tags and "tags" in when:
                    data["tags"] = sorted(when["tags"])
                if include_phase and "phase" in when:
                    data["phase"] = when["phase"]
                if include_ctx and "ctx" in job and job["ctx"] is not None:
                    data["ctx"] = job["ctx"]
            jobs_payload.append(data)
        return {"jobs": jobs_payload}

    return _with_error_handling(build, format)


def list_phases(
    include_docs: bool = False,
    include_deps: bool = False,
    include_jobs: bool = False,
    format: Format = "yaml",
) -> str:
    """List phases from the active runem config."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        if not (include_docs or include_deps or include_jobs):
            return {"phases": list(metadata.phases)}
        phases_payload = []
        for order, phase in enumerate(metadata.phases):
            data: typing.Dict[str, JsonLike] = {"name": phase}
            if include_docs:
                data["order"] = order
                data["description"] = "runem phase"
            if include_deps:
                data["deps"] = list(metadata.phases[:order])
            if include_jobs:
                data["jobs"] = [_job_name(job) for job in metadata.jobs[phase]]
            phases_payload.append(data)
        return {"phases": phases_payload}

    return _with_error_handling(build, format)


def list_tags(
    include_regex: bool = False,
    include_jobs: bool = False,
    format: Format = "yaml",
) -> str:
    """List tags from the active runem config."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        if not (include_regex or include_jobs):
            return {"tags": sorted(metadata.all_job_tags)}
        payload = []
        for tag in sorted(metadata.all_job_tags):
            data: typing.Dict[str, JsonLike] = {"name": tag}
            if include_regex and tag in metadata.file_filters:
                data["regex"] = metadata.file_filters[tag].get("regex")
            if include_jobs:
                data["jobs"] = [
                    _job_name(job)
                    for job in _all_jobs(metadata)
                    if tag in (Job.get_job_tags(job) or set())
                ]
            payload.append(data)
        return {"tags": payload}

    return _with_error_handling(build, format)


def list_filters(
    include_regex: bool = False,
    include_tag: bool = False,
    include_jobs: bool = False,
    format: Format = "yaml",
) -> str:
    """List file filters from the active runem config."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        if not (include_regex or include_tag or include_jobs):
            return {"filters": sorted(metadata.file_filters.keys())}
        payload = []
        for tag, file_filter in sorted(metadata.file_filters.items()):
            data: typing.Dict[str, JsonLike] = {"name": tag}
            if include_regex:
                data["regex"] = file_filter.get("regex")
            if include_tag:
                data["tag"] = file_filter.get("tag", tag)
            if include_jobs:
                data["jobs"] = [
                    _job_name(job)
                    for job in _all_jobs(metadata)
                    if tag in (Job.get_job_tags(job) or set())
                ]
            payload.append(data)
        return {"filters": payload}

    return _with_error_handling(build, format)


def list_options(
    include_docs: bool = False,
    include_type: bool = True,
    format: Format = "yaml",
) -> str:
    """List runem options from the active config."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        payload = []
        for option in sorted(metadata.options_config, key=lambda item: item["name"]):
            data: typing.Dict[str, JsonLike] = {
                "name": option["name"],
                "default": option.get("default"),
            }
            if include_type:
                data["type"] = option.get("type")
            if include_docs:
                for key in ("desc", "alias", "aliases"):
                    if key in option:
                        data[key] = typing.cast(JsonLike, option[key])
            payload.append(data)
        return {"options": payload}

    return _with_error_handling(build, format)


def _build_argv(
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
    options: typing.Optional[typing.Dict[str, object]],
    dry_run: bool,
) -> typing.List[str]:
    argv = ["runem", "--silent", "--no-spinner"]
    if jobs:
        argv.extend(["--jobs"] + jobs)
    if tags:
        argv.extend(["--tags"] + tags)
    if phases:
        argv.extend(["--phases"] + phases)
    for name, value in sorted((options or {}).items()):
        switch = "--%s" % name.replace("_", "-").replace(" ", "-")
        if value is False:
            switch = "--no-%s" % name.replace("_", "-").replace(" ", "-")
        if value is not None:
            argv.append(switch)
    return argv


def execute(
    jobs: typing.Optional[typing.List[str]] = None,
    tags: typing.Optional[typing.List[str]] = None,
    phases: typing.Optional[typing.List[str]] = None,
    options: typing.Optional[typing.Dict[str, object]] = None,
    dry_run: bool = False,
    format: Format = "yaml",
) -> str:
    """Execute runem or return the selected jobs for a dry-run."""

    def build() -> typing.Any:
        global LATEST_RUN_METADATA  # pylint: disable=global-statement
        metadata = _load_metadata()
        _validate_requested(metadata, jobs, tags, phases, options)
        if dry_run:
            selected = _filter_jobs_for_selection(metadata, jobs, tags, phases)
            return {
                "status": "dry_run",
                "selected_jobs": _selected_job_names(selected),
                "skipped_jobs": _skipped_job_names(metadata, selected),
                "failed_jobs": [],
                "reports": [],
                "timing": {},
            }

        argv = _build_argv(jobs, tags, phases, options, dry_run=False)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            run_metadata, job_run_metadatas, failure = _main(argv)
        LATEST_RUN_METADATA = job_run_metadatas
        return {
            "status": "failed" if failure else "ok",
            "selected_jobs": _executed_job_names(job_run_metadatas),
            "skipped_jobs": _skipped_job_names(
                run_metadata, _jobs_by_phase_from_metadata(job_run_metadatas)
            ),
            "failed_jobs": _failed_job_names(failure),
            "reports": _report_payload(job_run_metadatas, include_content=False),
            "timing": _timing_summary(job_run_metadatas),
            "stdout": _compact_text(stdout.getvalue()),
            "stderr": _compact_text(stderr.getvalue()),
        }

    return _with_error_handling(build, format)


def _selected_job_names(jobs_by_phase: PhaseGroupedJobs) -> typing.List[str]:
    names: typing.List[str] = []
    for phase in sorted(jobs_by_phase.keys()):
        names.extend(_job_name(job) for job in jobs_by_phase[phase])
    return sorted(names)


def _jobs_by_phase_from_metadata(
    job_run_metadatas: JobRunMetadatasByPhase,
) -> PhaseGroupedJobs:
    grouped: PhaseGroupedJobs = defaultdict(list)
    for phase, metadatas in job_run_metadatas.items():
        if phase == "_app":
            continue
        for timing, _ in metadatas:
            grouped[phase].append({"label": timing["job"][0]})
    return grouped


def _executed_job_names(job_run_metadatas: JobRunMetadatasByPhase) -> typing.List[str]:
    names = []
    for phase, metadatas in job_run_metadatas.items():
        if phase == "_app":
            continue
        names.extend(timing["job"][0] for timing, _ in metadatas)
    return sorted(names)


def _skipped_job_names(
    metadata: ConfigMetadata, selected: PhaseGroupedJobs
) -> typing.List[str]:
    selected_names = set(_selected_job_names(selected))
    return sorted(
        _job_name(job)
        for job in _all_jobs(metadata)
        if _job_name(job) not in selected_names
    )


def _failed_job_names(failure: typing.Optional[BaseException]) -> typing.List[str]:
    if not failure:
        return []
    return [str(failure)]


def _report_payload(
    job_run_metadatas: JobRunMetadatasByPhase, include_content: bool
) -> typing.List[typing.Dict[str, JsonLike]]:
    reports: typing.List[typing.Dict[str, JsonLike]] = []
    for phase, metadatas in sorted(job_run_metadatas.items()):
        for timing, report in metadatas:
            if not report:
                continue
            for name, url in report.get("reportUrls", []):
                item: typing.Dict[str, JsonLike] = {
                    "phase": phase,
                    "job": timing["job"][0],
                    "name": name,
                    "path": str(url),
                }
                if include_content:
                    path = pathlib.Path(url)
                    if path.exists() and path.is_file():
                        item["content"] = _compact_text(
                            path.read_text(encoding="utf-8")
                        )
                reports.append(item)
    return reports


def _timing_summary(
    job_run_metadatas: JobRunMetadatasByPhase,
) -> typing.Dict[str, typing.List[typing.Dict[str, JsonLike]]]:
    timing: typing.Dict[str, typing.List[typing.Dict[str, JsonLike]]] = {}
    for phase, metadatas in sorted(job_run_metadatas.items()):
        phase_entries = []
        for job_timing, _ in metadatas:
            phase_entries.append(_timing_entry(phase, job_timing))
        timing[phase] = phase_entries
    return timing


def _timing_entry(phase: str, job_timing: JobTiming) -> typing.Dict[str, JsonLike]:
    name, duration = job_timing["job"]
    return {
        "phase": phase,
        "job": name,
        "duration": duration.total_seconds(),
        "status": "recorded",
        "commands": [
            {"sub_job": label, "duration": timing.total_seconds(), "status": "recorded"}
            for label, timing in job_timing["commands"]
        ],
    }


def _compact_text(text: str) -> str:
    text = text.strip()
    if len(text) <= MAX_CAPTURE_CHARS:
        return text
    return text[:MAX_CAPTURE_CHARS] + "\n... truncated ..."


def get_reports(
    job: typing.Optional[str] = None,
    latest_only: bool = True,
    include_content: bool = False,
    format: Format = "yaml",
) -> str:
    """Return report metadata from the latest runem execution in this process."""

    def build() -> typing.Any:
        _ = latest_only  # latest in-process run is the only retained run.
        reports = _report_payload(LATEST_RUN_METADATA or {}, include_content)
        if job:
            reports = [report for report in reports if report.get("job") == job]
        return {"reports": reports}

    return _with_error_handling(build, format)


def get_timing(
    run_id: typing.Optional[str] = None,
    phase: typing.Optional[str] = None,
    job: typing.Optional[str] = None,
    sub_job: typing.Optional[str] = None,
    format: Format = "yaml",
) -> str:
    """Return compact timing metadata from the latest runem execution."""

    def build() -> typing.Any:
        _ = run_id  # runem does not currently persist run identifiers.
        timing = _timing_summary(LATEST_RUN_METADATA or {})
        entries: typing.List[typing.Dict[str, JsonLike]] = []
        for phase_name, phase_entries in timing.items():
            if phase and phase_name != phase:
                continue
            for entry in phase_entries:
                if job and entry.get("job") != job:
                    continue
                if sub_job:
                    commands = [
                        command
                        for command in typing.cast(
                            typing.List[typing.Dict[str, JsonLike]],
                            entry.get("commands", []),
                        )
                        if command.get("sub_job") == sub_job
                    ]
                    if not commands:
                        continue
                    entry = dict(entry)
                    entry["commands"] = commands
                entries.append(entry)
        return {"timing": entries}

    return _with_error_handling(build, format)


def create_server() -> typing.Any:
    """Create the FastMCP server and register runem-only tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as err:
        raise RuntimeError(
            "The MCP package is required to run this server. Install with "
            "`python -m pip install mcp` in the environment that launches it."
        ) from err

    server = FastMCP("runem-runner")
    server.tool()(list_jobs)
    server.tool()(list_phases)
    server.tool()(list_tags)
    server.tool()(list_filters)
    server.tool()(list_options)
    server.tool()(execute)
    server.tool()(get_reports)
    server.tool()(get_timing)
    return server


def main() -> None:
    """Run the MCP server."""
    create_server().run()


if __name__ == "__main__":
    main()
