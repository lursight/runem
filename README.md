<!-- [![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem) -->
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)
[![DOCS](https://lursight.github.io/runem/VIEW-DOCS-31c553.svg)](https://lursight.github.io/runem/)

# Run’em

**Describe your devops-tools, run them fast**

Run’em runs a project's dev-ops tasks, in parallel, and gives you a blueprint of what those tasks are. Commands are instantly discoverable, run in parallel, and easily extensible.

## Why Run’em?

- **Jobs Manifest** - discover tasks & onboard smoothly
- **Parallel**  - get results quicker
- **Simple**  - define task easily
- **Extensible** - add tasks, & reports quickly
- **Filters** - powerful task selection
- **Visibility** - see what you're running, & discover improvements.
- **Beautiful** - get graphs & metrics out of the box, then build custom reports.

## Highlights
### Jobs Manifest
The Jobs manifest (available via `runem --help`) gives you an overview and insights into all job and tasks for a project. A single source of truth for all tasks.

This allows faster on-boarding, easier discovery, and better team communication. It makes access and visibility of tasks easier and better.

### Parallel Execution:
Save time by running dev-ops tasks in parallel, and by getting metrics on those
runtimes.

Runem tries to run all tasks as quickly as possible, looking at resources, with
dependencies. 

NOTE: It is not yet a full resource analyser or dependency-execution graph, but by version
1.0.0 it will be.

### Filtering:
Use powerful and flexible filtering. Select or excluded tasks by `tags`, `name` and
`phase`. Chose the task to be run based on your needs, right now.

You can also customise filtering by adding your own command `options`.

See `--tags`, `--not-tags`, `--jobs`, `--not-jobs`, `--phases` and `--not-phases`.

### Powerful Insights
Understand what ran, how fast, and what failed.

**Quiet by Default:** Focus on what matters, and reveal detail only when needed.

## Quick Start
**Install:**
```bash
pip install runem
```
**Define a task:**

```yaml
`# .runem.yml
 - job:
    command: echo "hello world!"
```

**Run:**

```bash
runem
```

Run multiple commands in parallel, see timing, and keep output minimal. Need detail?

```bash
runem --verbose
```

[Quick Start Docs](https://lursight.github.io/runem/quick_start/)

## Basic Use

Typical workflows are running all default jobs, filtering and viewing the job manifest & help:
[Filter](https://lursight.github.io/runem/filtering/)
`runem --help` is your radar—instantly mapping out every available task:
[Help & Job Discovery](https://lursight.github.io/runem/help/)

## Configuration File

How and why to configure your projects `.runem.yml` file. How to scale up with multi-phase configs, how to apply filters and how to configure runtime options:
[Configuration](https://lursight.github.io/runem/configuration/)

## Default and Custom Reports

`runem` gives you basic performance metrics by default, and allows custom reporting like code-coverage, or profiling reports:
[Reports](https://lursight.github.io/runem/reports/)

## Troubleshooting

Swift solutions to common issues:
[Troubleshooting & Known Issues](https://lursight.github.io/runem/troubleshooting/)

---

## Contribute & Support

Brought to you by [Lursight Ltd.](https://lursight.com) and an open community.
[CONTRIBUTING.md](CONTRIBUTING.md)
[❤️ Sponsor](https://github.com/sponsors/lursight/)

## About Run’em

Run’em exists to accelerate your team’s delivery and reduce complexity. Learn about our [Mission](https://lursight.github.io/runem/mission/).

