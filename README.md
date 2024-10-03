<!-- [![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem) -->
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)
[![DOCS](https://lursight.github.io/runem/docs/VIEW-DOCS-31c553.svg)](https://lursight.github.io/runem/)

# Run'em: Accelerate Your Development Workflow
**Boost Efficiency and Save Time**
Runem is a flexible, multi-process tool designed to speed up your everyday tasks by running them in parallel. Whether you're testing, linting, or deploying, runem helps you work smarter and faster.

## Why Choose Run'em?
- **Streamlined Task Management**: Configure tasks with ease using declarative .runem.yml files.
- **Multiprocess Execution**: Run multiple tasks simultaneously, minimizing wall-clock time.
- **Optimized for Monorepos**: Supports multiple projects and task types, with easy filtering and configuration.
- **Detailed Reporting**: Get insights into task execution time and efficiency gains.

## Contents
- [Run'em: Accelerate Your Development Workflow](#runem-accelerate-your-development-workflow)
  - [Why Choose Run'em?](#why-choose-runem)
  - [Contents](#contents)
- [Features At A Glance:](#features-at-a-glance)
- [Using Run'em](#using-runem)
  - [Installation](#installation)
  - [Quick-start](#quick-start)
  - [Basic quick-start](#basic-quick-start)
    - [A more complete quick-start](#a-more-complete-quick-start)
  - [Basic Use](#basic-use)
  - [Advanced Use](#advanced-use)
    - [Advanced configuration options](#advanced-configuration-options)
    - [Custom reports](#custom-reports)
- [Help and job discovery](#help-and-job-discovery)
- [Troubleshooting](#troubleshooting)
- [Contributing to and supporting runem](#contributing-to-and-supporting-runem)
  - [Development](#development)
  - [Sponsor](#sponsor)
- [About runem](#about-runem)


# Features At A Glance:
- **Tagging**: Easily run specific job groups (e.g., lint, test, python).
- **Phases**: Organize tasks by phase (e.g., edit, test, deploy).
- **Configurable Options**: Customize how jobs are executed using simple options.
- **Declarative**: Jobs are define using simple YAML in [.runem.yml](https://lursight.github.io/runem/docs/configuration.html) .

# Using Run'em

## Installation

```bash
pip install runem
```

## Quick-start

## Basic quick-start
Create the following `.runem.yml` file at the root of your project:

```yml
- job:
    command: echo "hello world!"
```

Then anywhere in your project run `runem` to see how and when that task is run, and how long it took:
```bash
runem
```

To see the actual log output you will need to use `--verbose` as `runem` hides anything that isn't important. Only failures and reports are considered important.
```bash
# Or, to see "hello world!", use --verbose
runem --verbose  # add --verbose to see the actual output
```

To see how you can control your job use `--help`:
```bash
runem --help
```

### A more complete quick-start

See [quick-start docs](https://lursight.github.io/runem/docs/quick_start.html) for more quick-start tips.

## Basic Use

See [docs on basic use and use-cases](https://lursight.github.io/runem/docs/basic_use.html) for a comprehensive introduction.

## Advanced Use

### Advanced configuration options
See [configuration docs](https://lursight.github.io/runem/docs/configuration.html) for advanced configuration and use.

### Custom reports
See [reporting docs](https://lursight.github.io/runem/docs/reports.html) for more information on how reporting works.


# Help and job discovery

`--help` is designed to help your team discover what jobs and tasks they can automated. Read more at 
[help and discovery docs](https://lursight.github.io/runem/docs/help_and_job_discovery.html).

# Troubleshooting

See [troubleshooting and known issues docs](https://lursight.github.io/runem/docs/troubleshooting_known_issues.html).

---
# Contributing to and supporting runem

Awesome runem created by lursight

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Sponsor

[❤️ Sponsor this project](https://github.com/sponsors/lursight/)

# About runem
The runem mission is to improve developer velocity at
[Lursight Ltd.](https://lursight.com), read more about the runem
[mission](https://lursight.github.io/runem/docs/mission.html).

