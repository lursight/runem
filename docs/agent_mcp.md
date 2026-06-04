# Agent MCP server

Run'em includes a small MCP server for coding agents that need to inspect or run
the active `.runem.yml` with low token usage.

Use the MCP server instead of scraping `runem --help` when an agent needs
structured access to jobs, phases, tags, filters, options, reports, or timing.

## Discoverability

For agent-facing guidance from the CLI:

```bash
runem --help-agents
```

For the normal project-specific job manifest:

```bash
runem --help
```

## Running the server

Install `runem`, then launch:

```bash
runem-mcp
```

During local development from a checkout:

```bash
python -m runem.mcp.runner
```

The server should be started from a runem project root, or from a directory under
one. It uses the same `.runem.yml` discovery logic as `runem`.

## Tools

The server exposes these tools:

- `get_run_ctx`: returns the active runem root directory and config file path.
- `list_jobs`: lists jobs. Defaults to names only in compact YAML.
- `list_phases`: lists phases. Defaults to phase names only.
- `list_tags`: lists tags. Defaults to tag names only.
- `list_filters`: lists file filters. Defaults to filter names only.
- `list_options`: lists configured options and defaults.
- `execute`: runs selected jobs, tags, or phases, or returns a dry-run summary.
- `get_reports`: returns report metadata from the latest in-process execution.
- `get_timing`: returns timing metadata from the latest in-process execution.

Most tools default to compact YAML. Pass `format="json"` when JSON is more
convenient for the client.

## Recommended agent workflow

1. Call `get_run_ctx` to confirm the root and config file.
2. Call `list_jobs`, `list_phases`, `list_tags`, `list_filters`, or
   `list_options` with defaults for compact identifiers.
3. Request richer documentation only with explicit `include_*` flags.
4. Call `execute` with `dry_run=True` before broad or expensive runs.
5. Call `execute` without `dry_run` for the chosen run.
6. Call `get_reports` or `get_timing` only when report or timing summaries are
   needed.

## Output shape

Default responses are intentionally small. For example:

```yaml
jobs:
  - name: build
  - name: test
```

Richer metadata is available through explicit flags such as
`include_docs=True`, `include_jobs=True`, `include_regex=True`, and
`include_content=True`.

## Safety model

The server is read-only with respect to config files. It may execute `runem`,
read generated reports, and read timing/run metadata. It does not edit
`.runem.yml`, `.runem.local.yml`, or `.runem.user.yml`.

The `execute` tool validates requested jobs, tags, phases, and options before
running where possible. It calls runem's Python execution path directly rather
than shelling out.
