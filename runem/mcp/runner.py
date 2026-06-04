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


class RunemMcpError(RuntimeError):  # pragma: FIXME: add code coverage
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


def _normalise(  # pylint: disable=too-many-return-statements
    value: typing.Any,
) -> JsonLike:  # pragma: FIXME: add code coverage
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


def _serialise(
    payload: typing.Any,
    output_format: Format,
) -> str:  # pragma: FIXME: add code coverage
    normalised = _normalise(payload)
    if output_format == "json":
        return json.dumps(normalised, indent=2, sort_keys=True)
    return yaml.safe_dump(normalised, sort_keys=True)


def _with_error_handling(
    func: typing.Callable[[], typing.Any], output_format: Format
) -> str:  # pragma: FIXME: add code coverage
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


def _load_metadata() -> ConfigMetadata:  # pragma: FIXME: add code coverage
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


def _compact_job(
    job: JobConfig,
    include_docs: bool,
) -> typing.Dict[str, JsonLike]:  # pragma: FIXME: add code coverage
    data: typing.Dict[str, JsonLike] = {"name": _job_name(job)}
    when = typing.cast(typing.Dict[str, typing.Any], job.get("when", {}))
    if "tags" in when:
        data["tags"] = typing.cast(JsonLike, list(sorted(when["tags"])))
    if "phase" in when:
        data["phase"] = typing.cast(JsonLike, when["phase"])
    if "ctx" in job and job["ctx"] is not None:
        data["ctx"] = typing.cast(JsonLike, job["ctx"])
    if include_docs:
        if "label" in job:
            data["description"] = typing.cast(JsonLike, job["label"])
        if "command" in job:
            data["command"] = typing.cast(JsonLike, job["command"])
        if "module" in job:
            data["module"] = typing.cast(JsonLike, job["module"])
        if "addr" in job:
            data["function"] = typing.cast(JsonLike, job["addr"])
    return data


def _filter_jobs_for_selection(
    metadata: ConfigMetadata,
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
) -> PhaseGroupedJobs:  # pragma: FIXME: add code coverage
    argv = _build_argv(jobs, tags, phases, None, dry_run=True)
    parsed = parse_args(metadata, argv)
    return filter_jobs(parsed)


def _validate_requested(
    metadata: ConfigMetadata,
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
    options: typing.Optional[typing.Dict[str, object]],
) -> None:  # pragma: FIXME: add code coverage
    _validate_names("job", jobs, metadata.all_job_names)
    _validate_names("tag", tags, metadata.all_job_tags)
    _validate_names("phase", phases, metadata.all_job_phases)
    option_names = {
        option.get("name", "")
        for option in metadata.options_config
        if option.get("name", None)
    }
    _validate_names("option", list(options or {}), option_names)


def _validate_names(
    kind: str, requested: typing.Optional[typing.List[str]], available: typing.Set[str]
) -> None:  # pragma: FIXME: add code coverage
    invalid = sorted(set(requested or []) - available)
    if invalid:
        raise RunemMcpError(
            f"invalid_{kind}",
            f"Unknown '{kind}' value(s): {', '.join(invalid)}",
            f"Choose from: {', '.join(sorted(available))}",
        )


def list_jobs(
    include_docs: bool = False,
    names_only: bool = False,
    include_tags: bool = False,
    include_ctx: bool = False,
    include_phase: bool = False,
    fmt: Format = "yaml",
) -> str:
    """List jobs from the active runem config."""

    def build() -> typing.Any:  # pragma: FIXME: add code coverage
        metadata = _load_metadata()
        if names_only:
            return {"jobs": [_job_name(job) for job in _all_jobs(metadata)]}
        jobs_payload: typing.List[typing.Dict[str, JsonLike]] = []
        for job in _all_jobs(metadata):
            data: typing.Dict[str, JsonLike]
            if include_docs:
                data = _compact_job(job, include_docs=True)
            else:
                data = {"name": _job_name(job)}
                when = typing.cast(typing.Dict[str, typing.Any], job.get("when", {}))
                if include_tags and "tags" in when:
                    data["tags"] = typing.cast(JsonLike, sorted(when["tags"]))
                if include_phase and "phase" in when:
                    data["phase"] = typing.cast(JsonLike, when["phase"])
                if include_ctx and "ctx" in job and job["ctx"] is not None:
                    data["ctx"] = typing.cast(JsonLike, job["ctx"])
            jobs_payload.append(data)
        return {"jobs": jobs_payload}

    return _with_error_handling(build, fmt)


def list_phases(
    include_docs: bool = False,
    include_deps: bool = False,
    include_jobs: bool = False,
    fmt: Format = "yaml",
) -> str:
    """List phases from the active runem config."""

    def build() -> typing.Any:  # pragma: FIXME: add code coverage
        metadata = _load_metadata()
        if not (include_docs or include_deps or include_jobs):
            return {"phases": list(metadata.phases)}
        phases_payload: typing.List[typing.Dict[str, JsonLike]] = []
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

    return _with_error_handling(build, fmt)


def list_tags(
    include_regex: bool = False,
    include_jobs: bool = False,
    fmt: Format = "yaml",
) -> str:
    """List tags from the active runem config."""

    def build() -> typing.Any:  # pragma: FIXME: add code coverage
        metadata = _load_metadata()
        if not (include_regex or include_jobs):
            return {"tags": sorted(metadata.all_job_tags)}
        payload: typing.List[typing.Dict[str, JsonLike]] = []
        for tag in sorted(metadata.all_job_tags):
            data: typing.Dict[str, JsonLike] = {"name": tag}
            if include_regex and tag in metadata.file_filters:
                data["regex"] = typing.cast(
                    JsonLike, metadata.file_filters[tag].get("regex")
                )
            if include_jobs:
                data["jobs"] = [
                    _job_name(job)
                    for job in _all_jobs(metadata)
                    if tag in (Job.get_job_tags(job) or set())
                ]
            payload.append(data)
        return {"tags": payload}

    return _with_error_handling(build, fmt)


def list_filters(
    include_regex: bool = False,
    include_tag: bool = False,
    include_jobs: bool = False,
    fmt: Format = "yaml",
) -> str:
    """List file filters from the active runem config."""

    def build() -> typing.Any:  # pragma: FIXME: add code coverage
        metadata = _load_metadata()
        if not (include_regex or include_tag or include_jobs):
            return {"filters": sorted(metadata.file_filters.keys())}
        payload: typing.List[typing.Dict[str, JsonLike]] = []
        for tag, file_filter in sorted(metadata.file_filters.items()):
            data: typing.Dict[str, JsonLike] = {"name": tag}
            if include_regex:
                data["regex"] = typing.cast(JsonLike, file_filter.get("regex"))
            if include_tag:
                data["tag"] = typing.cast(JsonLike, file_filter.get("tag", tag))
            if include_jobs:
                data["jobs"] = [
                    _job_name(job)
                    for job in _all_jobs(metadata)
                    if tag in (Job.get_job_tags(job) or set())
                ]
            payload.append(data)
        return {"filters": payload}

    return _with_error_handling(build, fmt)


def list_options(
    include_docs: bool = False,
    include_type: bool = True,
    fmt: Format = "yaml",
) -> str:
    """List runem options from the active config."""

    def build() -> typing.Any:  # pragma: FIXME: add code coverage
        metadata = _load_metadata()
        payload: typing.List[typing.Dict[str, JsonLike]] = []
        for option in sorted(metadata.options_config, key=lambda item: item["name"]):
            data: typing.Dict[str, JsonLike] = {
                "name": typing.cast(JsonLike, option["name"]),
                "default": typing.cast(JsonLike, option.get("default")),
            }
            if include_type:
                data["type"] = typing.cast(JsonLike, option.get("type"))
            if include_docs:
                for key in ("desc", "alias", "aliases"):
                    if key in option:
                        data[key] = typing.cast(
                            JsonLike,
                            option[key],  # type: ignore
                        )
            payload.append(data)
        return {"options": payload}

    return _with_error_handling(build, fmt)


def get_run_ctx(fmt: Format = "yaml") -> str:
    """Return the active runem root directory and config file path."""

    def build() -> typing.Any:
        metadata = _load_metadata()
        return {
            "run_ctx": {
                "pwd": metadata.cfg_filepath.parent,
                "config_file": metadata.cfg_filepath,
            }
        }

    return _with_error_handling(build, fmt)


def _build_argv(
    jobs: typing.Optional[typing.List[str]],
    tags: typing.Optional[typing.List[str]],
    phases: typing.Optional[typing.List[str]],
    options: typing.Optional[typing.Dict[str, object]],
    dry_run: bool,
) -> typing.List[str]:  # pragma: FIXME: add code coverage
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
    fmt: Format = "yaml",
) -> str:  # pragma: FIXME: add code coverage
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

    return _with_error_handling(build, fmt)


def _selected_job_names(
    jobs_by_phase: PhaseGroupedJobs,
) -> typing.List[str]:  # pragma: FIXME: add code coverage
    names: typing.List[str] = []
    for phase in sorted(jobs_by_phase.keys()):
        names.extend(_job_name(job) for job in jobs_by_phase[phase])
    return sorted(names)


def _jobs_by_phase_from_metadata(
    job_run_metadatas: JobRunMetadatasByPhase,
) -> PhaseGroupedJobs:  # pragma: FIXME: add code coverage
    grouped: PhaseGroupedJobs = defaultdict(list)
    for phase, metadatas in job_run_metadatas.items():
        if phase == "_app":
            continue
        for timing, _ in metadatas:
            grouped[phase].append(typing.cast(JobConfig, {"label": timing["job"][0]}))
    return grouped


def _executed_job_names(
    job_run_metadatas: JobRunMetadatasByPhase,
) -> typing.List[str]:  # pragma: FIXME: add code coverage
    names: typing.List[str] = []
    for phase, metadatas in job_run_metadatas.items():
        if phase == "_app":
            continue
        names.extend(timing["job"][0] for timing, _ in metadatas)
    return sorted(names)


def _skipped_job_names(
    metadata: ConfigMetadata, selected: PhaseGroupedJobs
) -> typing.List[str]:  # pragma: FIXME: add code coverage
    selected_names = set(_selected_job_names(selected))
    return sorted(
        _job_name(job)
        for job in _all_jobs(metadata)
        if _job_name(job) not in selected_names
    )


def _failed_job_names(
    failure: typing.Optional[BaseException],
) -> typing.List[str]:  # pragma: FIXME: add code coverage
    if not failure:
        return []
    return [str(failure)]


def _report_payload(
    job_run_metadatas: JobRunMetadatasByPhase, include_content: bool
) -> typing.List[typing.Dict[str, JsonLike]]:  # pragma: FIXME: add code coverage
    reports: typing.List[typing.Dict[str, JsonLike]] = []
    for phase, metadatas in sorted(job_run_metadatas.items()):
        for timing, report in metadatas:
            if not report:
                continue
            for name, url in typing.cast(
                typing.Iterable[typing.Tuple[str, pathlib.Path]],
                report.get("reportUrls", []),
            ):
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
        phase_entries: typing.List[typing.Dict[str, JsonLike]] = []
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
            {
                "sub_job": label,
                "duration": timing.total_seconds(),
                "status": "recorded",
            }
            for label, timing in job_timing["commands"]
        ],
    }


def _compact_text(text: str) -> str:  # pragma: FIXME: add code coverage
    text = text.strip()
    if len(text) <= MAX_CAPTURE_CHARS:
        return text
    return text[:MAX_CAPTURE_CHARS] + "\n... truncated ..."


def get_reports(
    job: typing.Optional[str] = None,
    latest_only: bool = True,
    include_content: bool = False,
    fmt: Format = "yaml",
) -> str:  # pragma: FIXME: add code coverage
    """Return report metadata from the latest runem execution in this process."""

    def build() -> typing.Any:
        _ = latest_only  # latest in-process run is the only retained run.
        reports = _report_payload(LATEST_RUN_METADATA or {}, include_content)
        if job:
            reports = [report for report in reports if report.get("job") == job]
        return {"reports": reports}

    return _with_error_handling(build, fmt)


def get_timing(
    run_id: typing.Optional[str] = None,
    phase: typing.Optional[str] = None,
    job: typing.Optional[str] = None,
    sub_job: typing.Optional[str] = None,
    fmt: Format = "yaml",
) -> str:
    """Return compact timing metadata from the latest runem execution."""

    def build() -> typing.Any:
        _ = run_id  # runem does not currently persist run identifiers.
        timing = _timing_summary(LATEST_RUN_METADATA or {})
        entries: typing.List[typing.Dict[str, JsonLike]] = []
        for (
            phase_name,
            phase_entries,
        ) in timing.items():  # pragma: FIXME: add code coverage
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
                    entry["commands"] = typing.cast(JsonLike, commands)
                entries.append(entry)
        return {"timing": entries}

    return _with_error_handling(build, fmt)


def create_server() -> typing.Any:  # pragma: FIXME: add code coverage
    """Create the FastMCP server and register runem-only tools."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as err:
        raise RuntimeError(
            "The MCP package is required to run this server. Reinstall runem with "
            "its project dependencies in the environment that launches it."
        ) from err

    server = FastMCP("runem-runner")
    server.tool()(list_jobs)
    server.tool()(list_phases)
    server.tool()(list_tags)
    server.tool()(list_filters)
    server.tool()(list_options)
    server.tool()(get_run_ctx)
    server.tool()(execute)
    server.tool()(get_reports)
    server.tool()(get_timing)
    return server


def main() -> None:  # pragma: FIXME: add code coverage
    """Run the MCP server."""
    create_server().run()


if __name__ == "__main__":
    main()
