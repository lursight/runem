<!-- [![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem) -->
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)
[![DOCS](https://lursight.github.io/runem/docs/VIEW-DOCS-31c553.svg)](https://lursight.github.io/runem/)

# Run’em

**Describe you devop-tools, run them fast**

Run’em runs a project's dev-ops tasks, in parallel, and gives you a blueprint of what those tasks are. Commands are instantly discoverable, run in parallel, and easily extensible.

## Why Run’em?

- **Jobs Manifest** - discover tasks and onboard smoothly
- **Parallel**  - get results quicker
- **Simple**  - define task easily
- **Extensible** - add tasks quickly
- **Filters** - powerful task selection
- **Beautiful** - see metrics and graphs on tasks run times.

## Contents
- [Run’em](#runem)
  - [Core Strengths](#core-strengths)
  - [Why Run’em?](#why-runem)
  - [Contents](#contents)
- [Highlights](#highlights)
- [Quick Start](#quick-start)
- [Basic Use](#basic-use)
- [Advanced Use](#advanced-use)
- [Help & Discovery](#help--discovery)
- [Troubleshooting](#troubleshooting)
- [Contribute & Support](#contribute--support)
- [About Run’em](#about-runem)

# Highlights
## Jobs Manifest
The Jobs manifest (available via `--help`) gives you an overview and insights into all job and tasks for a project. A single source of truth for all tasks.

This allows faster onboarding, and better communication between teams. It makes access and visibility of tasks easier and better.

## Parallel Execution:
Save time by running dev-ops tasks in parallel, and by getting metrics on those
runtimes.

Runem tries to run all tasks as quickly as possible, looking at resources, with
dependencies. 

NOTE: It is not yet a full dependency-execution graph, but by version
1.0.0 it will be.

## Filtering:
Use powerful and flexible filtering. Select or excluded tasks by `tags`, `name` and
`phase`. Chose the task to be run based on your needs, right now.

You can also customise filtering by adding your own command `options`.

See `--tags`, `--not-tags`, `--jobs`, `--not-jobs`, `--phases` and `--not-phases`.

## Powerful Insights
Understand what ran, how fast, and what failed.

**Quiet by Default:** Focus on what matters, and reveal detail only when needed.

# Quick Start
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

[Quick Start Docs](https://lursight.github.io/runem/docs/quick_start.html)

# Basic Use

Get comfortable with typical workflows:
[Filter](https://lursight.github.io/runem/docs/basic_use.html)
`runem --help` is your radar—instantly mapping out every available task:
[Help & Job Discovery](https://lursight.github.io/runem/docs/help_and_job_discovery.html)

# Advanced Use

Scale up with multi-phase configs, filtered execution, and custom reporting:
[Advanced Configuration](https://lursight.github.io/runem/docs/configuration.html)
[Custom Reporting](https://lursight.github.io/runem/docs/reports.html)

# Troubleshooting

Swift solutions to common issues:
[Troubleshooting & Known Issues](https://lursight.github.io/runem/docs/troubleshooting_known_issues.html)

---

# Contribute & Support

Brought to you by [Lursight Ltd.](https://lursight.com) and an open community.
[CONTRIBUTING.md](CONTRIBUTING.md)
[❤️ Sponsor](https://github.com/sponsors/lursight/)

# About Run’em

Run’em exists to accelerate your team’s delivery and reduce complexity. Learn about our [Mission](https://lursight.github.io/runem/docs/mission.html).

