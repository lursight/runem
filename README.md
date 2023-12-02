# Run 'em: Run your developer-local tasks faster

## 1. Overview

`runem` (run 'em) is a utility designed to optimise the process of running developer jobs concurrently.

Job definitions are declarative and simple and the reports show how long each job took. 

The name "runem" is derived from the fusion of "run" and "them," encapsulating the essence of executing tasks seamlessly.

- [Run 'em: Run your developer-local tasks faster](#run-em-run-your-developer-local-tasks-faster)
  - [1. Overview](#1-overview)
  - [2. Features](#2-features)
  - [3. Installation](#3-installation)
  - [4. Basic Usage](#4-basic-usage)
    - [4.1. Tag filters](#41-tag-filters)
      - [4.1.1. Run jobs only with the 'lint' tag:](#411-run-jobs-only-with-the-lint-tag)
      - [4.1.2. If you want to lint all code _except_ nodejs code (and you have the appropriate tags):](#412-if-you-want-to-lint-all-code-except-nodejs-code-and-you-have-the-appropriate-tags)
      - [4.1.3. Run fast checks on `pre-commit`](#413-run-fast-checks-on-pre-commit)
    - [4.2. phase filters](#42-phase-filters)
      - [4.2.1 Focus on a phase](#421-focus-on-a-phase)
      - [4.2.2 Exclude slow phases temporarily](#422-exclude-slow-phases-temporarily)
  - [5. Using Help to get an Overview of Your Jobs](#5-using-help-to-get-an-overview-of-your-jobs)
  - [6. Configuration](#6-configuration)
    - [6.1. `config` - Run 'em global config](#61-config---run-em-global-config)
    - [6.2. `job` - Job config](#62-job---job-config)
- [Contributing to and supporting runem](#contributing-to-and-supporting-runem)
  - [Development](#development)
  - [Sponsor](#sponsor)


## 2. Features

- **Tagged Jobs:** Use tagging to define which type of jobs you want to run, be it `pre-commit`, `lint`, `test` or in multi-project codebases to split between running `python`, `node.js` or `c++` jobs, depending on the context you are working in!

- **Multiprocess Execution:** Leverage the power of multiprocessing for concurrent test job execution, optimizing efficiency and reducing runtime.
  
- **Data-Driven Test Management:** Drive your tests with data, making it easy to adapt and scale your testing suite to various scenarios, allowing you to execute, track, and analyze your dev-ops suite with ease.

## 3. Installation

```bash
pip install runem
```

## 4. Basic Usage

```bash
$ runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
        [--phases phaseX, phaseY] \
        [--MY-OPTION] [--not-MY-OPTION] 
#or
$ python -m runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
                  [--phases phaseX, phaseY] \
                  [--MY-OPTION] [--not-MY-OPTION] 
```

### 4.1. Tag filters
Jobs are tagged in the .runem.yml config file. Each unique tags is made available on the command-line. To see which tags are available use `--help`. To add a new tag extend the `tags` field in the `job` config.

You can control which types of jobs to run via tags. Just tag the job in the config and then from the command-line you can add `--tags` or `--not-tags` to refine exactly which jobs will be run. 

To debug why a job is not selected pass `--verbose`.

For example, if you have a `python` tagged job or jobs, to run only run those jobs you would do the following:

```bash
runem --tags python
```

`--tags` are exclusive filter in, that is the tags passed in replace are the only tags that are run. This allows one to focus on running just a subset of tags.

`--not-tags` are subtractive filter out, that is any job with these tags are not run, even if they have tags set via the `--tags` switch. Meaning you can choose to run `python` tagged job but not run the `lint` jobs with `--tags python --not-tags lint`, and so on.

#### 4.1.1. Run jobs only with the 'lint' tag:

```bash
runem --tags lint
```

#### 4.1.2. If you want to lint all code _except_ nodejs code (and you have the appropriate tags):

```bash
runem --tags lint --not-tags deprecated
```

#### 4.1.3. Run fast checks on `pre-commit`

If you have fast jobs that tagged as appropriate for pre-commit hooks.

```bash
mkdir scripts/git-hooks
echo "runem --tags pre-commit" > scripts/git-hooks/pre-commit
# add the following to .git/config
# [core]
#   # ... existing config ...
#	  hooksPath = ./scripts/git-hooks/husky/
```

### 4.2. phase filters

Sometimes just want to run a specific phase, so you can focus on it and iterate quickly, within that context. 

#### 4.2.1 Focus on a phase

For example, if you have a `reformat` phase, you might want to run just `reformat` jobs phase whilst preparing a commit and are just preparing cosmetic changes e.g. updating comments, syntax, or docs.

```bash
runem --phase reformat
```

#### 4.2.2 Exclude slow phases temporarily

If you have 4 stages `bootstrap`, `pre-run`, `reformat`, `test` and `verify` phase, and are tightly iterating and focusing on the 'test-coverage' aspect of the test-phase, then you do not care about formatting as long as you can see your coverage results ASAP. However if your test-coverage starts passing then you will care about subsequent stages, so you can exclude the slower reformat-stage with the following and everything else will run.

```bash
runem --not-phase pre-run reformat
```

**Note:** The `--tags` and `--not-tags` options can be used in combination to further refine task execution based on your requirements.


## 5. Using Help to get an Overview of Your Jobs

The `--help` switch will show you a full list of all the configured job-tasks, the tags and the override options, describing how to configure a specific run.
```bash
$ python -m runem --help
#or
$ runem  --help
```

<details>
<summary>For example</summary>

```
usage: runem.py [-h] [--jobs JOBS [JOBS ...]] [--not-jobs JOBS_EXCLUDED [JOBS_EXCLUDED ...]] [--phases PHASES [PHASES ...]]
                [--not-phases PHASES_EXCLUDED [PHASES_EXCLUDED ...]] [--tags TAGS [TAGS ...]] [--not-tags TAGS_EXCLUDED [TAGS_EXCLUDED ...]]
                [--black] [--no-black] [--check-only] [--no-check-only] [--coverage] [--no-coverage] [--docformatter] [--no-docformatter]
                [--generate-call-graphs] [--no-generate-call-graphs] [--install-deps] [--no-install-deps] [--isort] [--no-isort] [--profile]
                [--no-profile] [--update-snapshots] [--no-update-snapshots] [--unit-test] [--no-unit-test] [--unit-test-firebase-data]
                [--no-unit-test-firebase-data] [--unit-test-python] [--no-unit-test-python] [--call-graphs | --no-call-graphs]
                [--procs PROCS] [--root ROOT_DIR] [--verbose | --no-verbose | -v]

Runs the Lursight Lang test-suite

options:
  -h, --help            show this help message and exit
  --call-graphs, --no-call-graphs
  --procs PROCS, -j PROCS
                        the number of concurrent test jobs to run, -1 runs all test jobs at the same time (8 cores available)
  --root ROOT_DIR       which dir to use as the base-dir for testing, defaults to checkout root
  --verbose, --no-verbose, -v

jobs:
  --jobs JOBS [JOBS ...]
                        List of job-names to run the given jobs. Other filters will modify this list. Defaults to '['flake8 py', 'install
                        python requirements', 'json validate', 'mypy py', 'pylint py', 'reformat py', 'spell check']'
  --not-jobs JOBS_EXCLUDED [JOBS_EXCLUDED ...]
                        List of job-names to NOT run. Defaults to empty. Available options are: '['flake8 py', 'install python requirements',
                        'json validate', 'mypy py', 'pylint py', 'reformat py', 'spell check']'

phases:
  --phases PHASES [PHASES ...]
                        Run only the phases passed in, and can be used to change the phase order. Phases are run in the order given. Defaults
                        to '{'edit', 'pre-run', 'analysis'}'.
  --not-phases PHASES_EXCLUDED [PHASES_EXCLUDED ...]
                        List of phases to NOT run. This option does not change the phase run order. Options are '['analysis', 'edit', 'pre-
                        run']'.

tags:
  --tags TAGS [TAGS ...]
                        Only jobs with the given tags. Defaults to '['json', 'lint', 'py', 'spell', 'type']'.
  --not-tags TAGS_EXCLUDED [TAGS_EXCLUDED ...]
                        Removes one or more tags from the list of job tags to be run. Options are '['json', 'lint', 'py', 'spell', 'type']'.

job-param overrides:
  --black               allow/disallows py-black from running
  --no-black            turn off allow/disallows py-black from running
  --check-only          runs in check-mode, erroring if isort, black or any text-edits would occur
  --no-check-only       turn off runs in check-mode, erroring if isort, black or any text-edits would occur
  --coverage            generates coverage reports for whatever can generate coverage info when added
  --no-coverage         turn off generates coverage reports for whatever can generate coverage info when added
  --docformatter        formats docs and comments in whatever job can do so
  --no-docformatter     turn off formats docs and comments in whatever job can do so
  --generate-call-graphs
                        Generates call-graphs in jobs that can
  --no-generate-call-graphs
                        turn off Generates call-graphs in jobs that can
  --install-deps        gets dep-installing job to run
  --no-install-deps     turn off gets dep-installing job to run
  --isort               allow/disallows isort from running on python files
  --no-isort            turn off allow/disallows isort from running on python files
  --profile             generate profile information in jobs that can
  --no-profile          turn off generate profile information in jobs that can
  --update-snapshots    update snapshots in jobs that can update data snapshots
  --no-update-snapshots
                        turn off update snapshots in jobs that can update data snapshots
  --unit-test           run unit tests
  --no-unit-test        turn off run unit tests
  --unit-test-firebase-data
                        run unit tests for the firebase function's data
  --no-unit-test-firebase-data
                        turn off run unit tests for the firebase function's data
  --unit-test-python    run unit tests for the python code
  --no-unit-test-python
                        turn off run unit tests for the python code
```
</details>

## 6. Configuration

`runem` searches for `.runem.yml` and will pre-load the command-line options with

Configuration is Yaml and consists of two main configurations, `config` and `job`:

- `config` describes how the jobs should be run.
- each `job`  entry describe a job-task, such and running unit-tests, linting or running any other type of command.

### 6.1. `config` - Run 'em global config

- **phases:** 
  - *Description:* Specifies the different phases of the testing process, in the order they are to be run. Each job will be run under a specific phase.
  - *Values:* A list of strings representing "phases" such as pre-run (e.g. bootstrapping), edit (running py-black or prettifier or clang-tools), and analysis (unit-tests, coverage, linting).

- **files:**
  - *Description:* Defines filters for categorizing files based on tags and regular expressions. Maps tags to files-to-be tested. If a job has one or more tags that map to file-filters that job will receive all files that match those filters.
  - *Values:* A list of dictionaries, each containing a 'filter' key with 'tag' and 'regex' subkeys.

- **options:**
  - *Description:* Configures various option-overrides for the job-tasks. Overrides can be set on the command line and accessed by jobs to turn on or off features such as 'check-only' or to opt out of sub-tasks.
  - *Values:* A list of dictionaries, each containing an 'option' key with 'default' boolean value, a 'name', a 'type', a 'desc', and optional 'alias' subkeys. NOTE: only 'bool' types are currently supported.

  - **default:** Specifies the default value of the option.
  - **name:** Represents the name of the option.
  - **type:** Indicates the data type of the option (e.g., bool for boolean).
  - **desc:** Provides a description of the option.
  - **alias:** (Optional) Provides an alias for the option if specified.

### 6.2. `job` - Job config
- **job:**
  - *Description:* Represents a specific job task that is to be run asynchronously.
  - *Fields:*
    - **addr:**
      - *Description:* Specifies the address details of the job, including the file and function.
      - *Subkeys:*
        - **file:** Indicates the file path of the job.
        - **function:** Indicates the function within the file that represents the job.
      - *Example:*
        ```yaml
        file: scripts/test-hooks/rust_wrappers.py
        function: _job_rust_code_reformat
        ```

    - **ctx:**
      - *Description:* Provides the execution context for the job, including the working directory and parameters.
      - *Subkeys:*
        - **cwd:** Specifies the working directory for the job.
        - **params:** Specifies parameters for the job.
      - *Example:*
        ```yaml
        cwd: .
        params:
          limitFilesToGroup: true
        ```

    - **label:**
      - *Description:* Assigns a label to the job for identification.
      - *Example:*
        ```yaml
        label: reformat py
        ```

    - **when:**
      - *Description:* Defines the conditions under which the job should run.
      - *Subkeys:*
        - **phase:** Specifies the testing phase in which the job should run.
        - **tags:** Specifies the tags associated with the job.
      - *Example:*
        ```yaml
        when:
          phase: edit
          tags:
            - py
            - format
        ```

  - *Example:*
    ```yaml
    - job:
        addr:
          file: scripts/test-hooks/nodejs.py
          function: _job_js_code_reformat
        ctx:
          cwd: src/subproject_4
          params:
            limitFilesToGroup: true
        label: reformat 
        when:
          phase: edit
          tags:
            - js
            - subproject4
            - pretty


---
# Contributing to and supporting runem

[![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem)
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)

Awesome runem created by lursight

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Sponsor

[❤️ Sponsor this project](https://github.com/sponsors/lursight/)
