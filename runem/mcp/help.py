"""Agent-facing help text for runem MCP integration."""


def help_agents_text() -> str:
    """Return concise guidance for agents discovering runem's MCP server."""
    return """runem agent integration

Use runem's MCP server when an agent needs low-token discovery or execution of
the active .runem.yml without scraping `runem --help` output.

Server command:
  runem-mcp

Development command:
  python -m runem.mcp.runner

Recommended agent workflow:
  1. Call get_run_ctx to confirm the runem root and config file.
  2. Call list_jobs, list_phases, list_tags, list_filters, or list_options with
     default arguments for compact identifiers.
  3. Request richer docs only with explicit include_* flags.
  4. Call execute with jobs, tags, phases, and options. Use dry_run=True before
     expensive or broad runs.
  5. Call get_reports or get_timing after execution when summaries are needed.

Tools:
  get_run_ctx, list_jobs, list_phases, list_tags, list_filters, list_options,
  execute, get_reports, get_timing

Docs:
  https://lursight.github.io/runem/agent_mcp/
"""
