---
name: runem
description: Run or configure runem (phases, jobs, tags). Use when running tests, lint, format, or CI workflows.
---

# runem

Run and configure runem for dev-ops tasks. Runem is the project's multi-process task runner (`.runem.yml`); job hooks live in `scripts/test_hooks/`.

## MCP-first execution

Prefer the runem MCP server when it is available:

- Use `mcp__runem.execute` for validation/format runs; pass `tags`, `phases`, `jobs`, and `options` instead of shell flags.
- Use `mcp__runem.list_jobs`, `list_phases`, `list_tags`, and `list_options` to inspect selectors before guessing.
- Use `mcp__runem.get_reports` / `get_timing` after runs when reporting results.
- If the runem MCP server/tool is not available or fails before selecting/running jobs, report that explicitly, then fall back to the equivalent `runem ...` shell command.
- Shell commands below are the fallback/reference form for the same selectors.

## When to use

- User asks to run tests, lint, format, or CI.
- User edits `.runem.yml` or `scripts/test_hooks/**`.
- User mentions phases, jobs, tags, or runem.

## Phases (order)

1. deps-upgrade → deps-install → pre-checks → edit → build → check → jest → verify → e2e-web → e2e-detox → post-checks

## Canonical validation (required before commit)

**Full test suite for a scope = runem, not in-package yarn test.** Relying only on `cd app/packages/lur-core && yarn test` has caused full-suite failures. See **development-validation-app.mdc** (app/) or **development-validation-web.mdc** (web_static/).

| Scope | Command |
|-------|--------|
| lur-core full suite | `runem --tags lur-core` |
| App packages (wider impact) | `runem --tags app` |

Before committing changes under `app/`, run `runem -f` first, then run `runem --tags lur-core` (lur-core only) or `runem --tags app` (app-wide). Do not rely only on `yarn test` from a package.

If runem fails in sandboxed agent execution with multiprocessing/socket permission errors, rerun with escalated permissions first; treat this as environment execution setup rather than a product-code failure signal.
If runem fails unexpectedly, first verify interpreter resolution before changing hooks/config:
`which runem`, `which python3`, `python3 -m ruff --version`, `runem --version`.
Prefer repo-local env when needed: `PATH="$(pwd)/.pyenv/bin:$PATH" runem ...`.
Agent may suggest edits to `.runem.yml` or `scripts/test_hooks/**`, but must ask for user confirmation before making those edits.

When unrelated WIP exists, validate commit-candidate content with staged-only flow: stage candidate files, `git stash --keep-index` non-staged changes, run canonical runem command, commit only on pass, then `git stash pop`.

## Common commands

MCP selector equivalents:

- Full suite: `{}`
- lur-core full suite: `{"tags":["lur-core"]}`
- App packages: `{"tags":["app"]}`
- Jest only: `{"tags":["jest"]}`
- Lint only: `{"tags":["lint"]}`
- Format only: `{"phases":["edit"]}`
- lur-core format: `{"phases":["edit"],"tags":["lur-core"]}`
- Single job: `{"jobs":["app:jest:lur-core"],"tags":["lur-core"]}`

```bash
runem                                    # full suite
runem --tags lur-core                    # lur-core full suite (canonical for lur-core changes)
runem --tags app                         # app packages only (format, lint, type-check, test)
runem --tags jest                        # unit tests only
runem --tags lint                        # lint only
runem --phases edit                      # format only
runem -f                                 # run on modified files only
runem --jobs "app:jest:lur-core"         # single job (see below: must pass tag too for jest)
runem --check-only                       # CI mode (error if format would change)
runem --tags e2e-app-lang-web --e2e-app-web --e2e-minimal --no-service-in-docker --verbose  # Playwright E2E
runem --jobs "detox:app-lang" --e2e-app-ios --e2e-minimal --no-service-in-docker --verbose   # Detox E2E
```

### Single-job Jest (tools learned)

When running **one** Jest job (e.g. `--jobs "app:jest:lur-core"`), you **must also pass that job’s tag** (e.g. `--tags lur-core`). Otherwise the job early-returns and Jest never runs (runem reports ~0 s). Example:

```bash
runem --jobs "app:jest:lur-core" --tags lur-core --runInBand           # single-threaded, with coverage
runem --jobs "app:jest:lur-core" --tags lur-core --runInBand --no-coverage  # single-threaded, no cov
```

Use **`--runInBand`** when you want single-threaded Jest (how runem/CI runs each package when multiple jest jobs run in parallel). Use **`--no-coverage`** for faster no-cov runs.

## Key jobs (labels)

| Label | Phase | Purpose |
|-------|--------|---------|
| `app:pretty` | edit | Prettier on app packages |
| `app:eslint` | check | ESLint on app packages |
| `app:typescript` | build | `tsc` on app-chat, app-lang, lur-core |
| `app:jest:run` | jest | Jest for app root workspace (raw coverage data) |
| `app:jest:coverage` | verify | Coverage merge/report generation for app root |
| `app:jest:lur-core` | jest | Jest for lur-core only (pass `--tags lur-core` when using `--jobs`) |
| `app:e2e:app-lang-web` | e2e-web | Playwright E2E |
| `detox:app-lang` | e2e-detox | Detox E2E |
| `www:build` | build | Next.js production build |

Install runem: `pip install runem` (or `pip install -e ".[tests]"` from repo root). Ensure app deps: `cd app && yarn install`.
