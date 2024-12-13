<!-- [![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem) -->
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)
[![DOCS](https://lursight.github.io/runem/docs/VIEW-DOCS-31c553.svg)](https://lursight.github.io/runem/)

# Run’em

**Your Blueprint of Commands. Your Engine of Parallel Execution.**
Run’em is your definitive blueprint of tasks and commands—instantly discoverable, effortlessly parallel, and elegantly extensible.

## Core Strengths

**Blueprint** - discover tasks and onboard smoothly\
**Parallel**  - get results quicker\
**Simple**  - define task easily\
**Extensible** - add tasks quickly\
**Filters** - powerful task selection\
**Reports** - see metrics on tasks

## Why Run’em?
- **Command Blueprint:** Instantly see and run all your tasks. No guesswork, no rummaging.
- **Effortless Parallelism:** Execute tasks side-by-side to obliterate downtime.
- **Simple YAML Declarations:** Define everything in one `.runem.yml`.
- **Extensible & Smart:** Adapt to monorepos, complex workflows, and evolving needs.
- **Discoverable by Design:** `runem --help` guides your team, new hires, or contributors to every defined command.

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
## Blueprint of Commands:
The blueprint (available via `--help`) gives you a manifest of all jobs and tasks in a
project. A single source of truth for all tasks.
## Parallel Execution:
Maximise speed with automatic concurrency. Runem tries to run all tasks as quickly as
possible, looking at resources, with dependencies. It is not yet a full
dependency-execution graph, but by version 1.0.0 it will be.
## Filtering:
Use powerful and flexible filtering. Select or excluded tasks by `tags`, `name` and
`phase`. Chose the task to be run based on your needs, right now.

You can also customise filtering by adding your own command `options`.

See `--tags`, `--not-tags`, `--jobs`, `--not-jobs`, `--phases` and `--not-phases`.
## Powerful Insights:** Understand what ran, how fast, and what failed.
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
[Basic Use Docs](https://lursight.github.io/runem/docs/basic_use.html)

# Advanced Use

Scale up with multi-phase configs, filtered execution, and custom reporting:
[Advanced Configuration](https://lursight.github.io/runem/docs/configuration.html)
[Custom Reporting](https://lursight.github.io/runem/docs/reports.html)

# Help & Discovery

`runem --help` is your radar—instantly mapping out every available task:
[Help & Job Discovery](https://lursight.github.io/runem/docs/help_and_job_discovery.html)

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

