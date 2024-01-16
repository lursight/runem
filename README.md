# Run 'em: Run your developer-local tasks faster

## 1. Overview

`runem` (run 'em) is a declarative tools designed to optimise the running of developer jobs concurrently.

`runem` is designed to be simple to use and easy to learn, but powerful to use.

Job definitions are declarative and simple and the reports show how long each job took, and how much time `runem` saved you.

The name "runem" is derived from the fusion of "run" and "them," encapsulating the essence of executing tasks quickly.

- [Run 'em: Run your developer-local tasks faster](#run-em-run-your-developer-local-tasks-faster)
  - [1. Overview](#1-overview)
  - [2. Features](#2-features)
  - [3. Installation](#3-installation)
  - [4 Quick start](#4-quick-start)
  - [4.1 A more complete Quick start](#41-a-more-complete-quick-start)
  - [5. Basic Usage](#5-basic-usage)
    - [5.1. Tag filters](#51-tag-filters)
      - [5.1.1. Run jobs only with the 'lint' tag:](#511-run-jobs-only-with-the-lint-tag)
      - [5.1.2. If you want to lint all code _except_ nodejs code (and you have the appropriate tags):](#512-if-you-want-to-lint-all-code-except-nodejs-code-and-you-have-the-appropriate-tags)
      - [5.1.3. Run fast checks on `pre-commit`](#513-run-fast-checks-on-pre-commit)
    - [5.2. phase filters](#52-phase-filters)
      - [5.2.1 Focus on a phase](#521-focus-on-a-phase)
      - [5.2.2 Exclude slow phases temporarily](#522-exclude-slow-phases-temporarily)
  - [6 Reports on your tasks](#6-reports-on-your-tasks)
    - [6.1 Task timings report](#61-task-timings-report)
    - [6.2 Bar-graphs with \`termplotlib\`\`](#62-bar-graphs-with-termplotlib)
  - [7. Using Help to get an Overview of Your Jobs](#7-using-help-to-get-an-overview-of-your-jobs)
  - [8. Configuration](#8-configuration)
    - [8.1. `config` - Run 'em global config](#81-config---run-em-global-config)
    - [8.2. `job` - Job config](#82-job---job-config)
  - [9. Troubleshooting \& Known issues](#9-troubleshooting--known-issues)
    - [9.1 I don't see bar graph timing reports!](#91-i-dont-see-bar-graph-timing-reports)
      - [Solution:](#solution)
    - [9.2 I can't specify a dependency!](#92-i-cant-specify-a-dependency)
      - [Solution](#solution-1)
    - [9.3 Why is there so much output on errors, it looks duplicated?](#93-why-is-there-so-much-output-on-errors-it-looks-duplicated)
      - [Solution](#solution-2)
    - [9.4 I can't see reports for job when errors happen!](#94-i-cant-see-reports-for-job-when-errors-happen)
      - [Solution](#solution-3)
    - [9.5 I want to see log output for tasks in real-time, as they're happening!](#95-i-want-to-see-log-output-for-tasks-in-real-time-as-theyre-happening)
      - [Solution](#solution-4)
- [Contributing to and supporting runem](#contributing-to-and-supporting-runem)
  - [Development](#development)
  - [Sponsor](#sponsor)


## 2. Features

- **Declarative Tasks** Describe all your tasks once, and optionally describe how and when to run them.

- **Tagged Jobs:** Use tagging to define which type of jobs you want to run, be it `pre-commit`, `lint`, `test` or in multi-project codebases to split between running `python`, `node.js` or `c++` jobs, depending on the context you are working in!

- **Multiprocess Execution:** Leverage the power of multiprocessing for concurrent test job execution, optimizing efficiency and reducing runtime.
  
- **Data-Driven Test Management:** Drive your tests with data, making it easy to adapt and scale your testing suite to various scenarios, allowing you to execute, track, and analyze your dev-ops suite with ease.

## 3. Installation

```bash
pip install runem
```

## 4 Quick start

Create the following `.runem.yml` file at the root of your project:

```yml
- job:
    command: echo "hello world!"
```

Then anywhere in your project run, to see how and when that task is run, and how long it took.
```sh
runem

# Or, to see "hello world!", use --verbose
runem --verbose  # add --verbose to see the actual output
```

To see how you can control your job use
```sh
runem --help
```

## 4.1 A more complete Quick start

Here's a simple setup for a python project.

Notice that this specifies:
-  The `phases` to use, and their order:
   - This shows how we can control tasks that edit the files can go before analysis 
   - This reduces any false-negatives the jobs may generate from running multiple jobs that may contend for write-access on the same files
   - NOTE: `phases` are an early-stage way:
     - To implement dependency chaining
       - There is no dependency linking between jobs, yet.
     - To manage resources
       - For example, if you have a task which is threaded and/or memory heavy, you may want to put that into its own phase to get faster output.
- `tags` to allow control over which jobs to run.
  - Also which files to pass to jobs.
- File-filters to detect which files the job operate on.
  - NOTE: this is a WIP feature
- Uses job-options:
   - Allowing a python-function-job to control it's sub-task/processes.
-  If you use `--help` you will see a summary of all controls available.

```yml
- config:
    phases:
      - edit
      - analysis
    files:
      - filter:
          tag: py
          regex: ".*\\.py$"
    options:
      - option:
          name: black
          default: true
          type: bool
          desc: allow/disallows py-black from running
      - option:
          name: docformatter
          default: true
          type: bool
          desc: formats docs and comments in whatever job can do so
      - option:
          name: check_only
          alias: check
          default: false
          type: bool
          desc: runs in check-mode, erroring if isort, black or any text-edits would occur
- job:
    command: pytest tests/
    when:
      phase: analysis
      tags:
        - py
- job:
    command: mypy my_project/ tests/
    when:
      phase: analysis
      tags:
        - py
- job:
    addr:
      file: runem_hooks/py.py
      function: _job_py_code_reformat
    label: reformat py
    when:
      phase: edit
      tags:
        - py
        - format
        - py format
```

The following python file accompanies the above configuration and does slightly more advanced work. The file contains:
- a single job.
- the job linearises edit tasks that would otherwise contend for write-access to the files they operate on.
  - formatting and doc-generation both edit files, conforming them to the coding standard.
- uses `options` (see the config section) to control whether to:
  - use `check-only` mode for CiCd, modifying the command-line switched passed down to the sub-commands.
  - control whether `python-black` and/or/nor `docformatter` is run.
- modifies the allowed-exit codes for `docformatter` to be `0` or `3`, matching the designed behaviour of that tool.

```py
# runem_hooks/py.py
# A file to do more advanced and conditional checking using the `runem` infrastructure.
import typing

from runem.log import log
from runem.run_command import RunCommandUnhandledError, run_command
from runem.types import FilePathList, JobName, JobReturnData, Options


def _job_py_code_reformat(
    **kwargs: typing.Any,
) -> None:
    """Runs python formatting code in serial order as one influences the other."""
    label: JobName = kwargs["label"]
    options: Options = kwargs["options"]
    python_files: FilePathList = kwargs["file_list"]

    # put into 'check' mode if requested on the command line
    extra_args = []
    docformatter_extra_args = [
        "--in-place",
    ]
    if "check_only" in options and options["check_only"]:
        extra_args.append("--check")
        docformatter_extra_args = []  # --inplace is not compatible with --check

    if "black" in options and options["black"]:
        black_cmd = [
            "python3",
            "-m",
            "black",
            *extra_args,
            *python_files,
        ]
        kwargs["label"] = f"{label} black"
        run_command(cmd=black_cmd, **kwargs)

    if "docformatter" in options and options["docformatter"]:
        docformatter_cmd = [
            "python3",
            "-m",
            "docformatter",
            "--wrap-summaries",
            "88",
            "--wrap-descriptions",
            "88",
            *docformatter_extra_args,
            *extra_args,
            *python_files,
        ]
        allowed_exits: typing.Tuple[int, ...] = (
            0,  # no work/change required
            3,  # no errors, but code was reformatted
        )
        if "check_only" in options and options["check_only"]:
            # in check it is ONLY ok if no work/change was required
            allowed_exits = (0,)
        kwargs["label"] = f"{label} docformatter"
        run_command(
            cmd=docformatter_cmd,
            ignore_fails=False,
            valid_exit_ids=allowed_exits,
            **kwargs,
        )
```

## 5. Basic Usage

```bash
$ runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
        [--phases phaseX, phaseY] \
        [--MY-OPTION] [--not-MY-OPTION] 
#or
$ python -m runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
                  [--phases phaseX, phaseY] \
                  [--MY-OPTION] [--not-MY-OPTION] 
```

### 5.1. Tag filters
Jobs are tagged in the .runem.yml config file. Each unique tags is made available on the command-line. To see which tags are available use `--help`. To add a new tag extend the `tags` field in the `job` config.

You can control which types of jobs to run via tags. Just tag the job in the config and then from the command-line you can add `--tags` or `--not-tags` to refine exactly which jobs will be run. 

To debug why a job is not selected pass `--verbose`.

For example, if you have a `python` tagged job or jobs, to run only run those jobs you would do the following:

```bash
runem --tags python
```

`--tags` are exclusive filter in, that is the tags passed in replace are the only tags that are run. This allows one to focus on running just a subset of tags.

`--not-tags` are subtractive filter out, that is any job with these tags are not run, even if they have tags set via the `--tags` switch. Meaning you can choose to run `python` tagged job but not run the `lint` jobs with `--tags python --not-tags lint`, and so on.

#### 5.1.1. Run jobs only with the 'lint' tag:

```bash
runem --tags lint
```

#### 5.1.2. If you want to lint all code _except_ nodejs code (and you have the appropriate tags):

```bash
runem --tags lint --not-tags deprecated
```

#### 5.1.3. Run fast checks on `pre-commit`

If you have fast jobs that tagged as appropriate for pre-commit hooks.

```bash
mkdir scripts/git-hooks
echo "runem --tags pre-commit" > scripts/git-hooks/pre-commit
# add the following to .git/config
# [core]
#   # ... existing config ...
#	  hooksPath = ./scripts/git-hooks/husky/
```

### 5.2. phase filters

Sometimes just want to run a specific phase, so you can focus on it and iterate quickly, within that context. 

#### 5.2.1 Focus on a phase

For example, if you have a `reformat` phase, you might want to run just `reformat` jobs phase whilst preparing a commit and are just preparing cosmetic changes e.g. updating comments, syntax, or docs.

```bash
runem --phase reformat
```

#### 5.2.2 Exclude slow phases temporarily

If you have 4 stages `bootstrap`, `pre-run`, `reformat`, `test` and `verify` phase, and are tightly iterating and focusing on the 'test-coverage' aspect of the test-phase, then you do not care about formatting as long as you can see your coverage results ASAP. However if your test-coverage starts passing then you will care about subsequent stages, so you can exclude the slower reformat-stage with the following and everything else will run.

```bash
runem --not-phase pre-run reformat
```

**Note:** The `--tags` and `--not-tags` options can be used in combination to further refine task execution based on your requirements.

## 6 Reports on your tasks

Runem has a built-in support for reporting on tasks

### 6.1 Task timings report

Runem will run the task and report how long the task took and whether it saved you any time, for example:

```text
# output from runem when run on runem's project, without `termplotlib`
runem: Running 'pre-run' with 2 workers (of 8 max) processing 2 jobs
runem: Running 'edit' with 1 workers (of 8 max) processing 1 jobs
runem: Running 'analysis' with 7 workers (of 8 max) processing 7 jobs
runem: reports:
runem: runem: 8.820488s
runem: ├runem.pre-build: 0.019031s
runem: ├runem.run-phases: 8.801317s
runem: ├pre-run (total): 0.00498s
runem: │├pre-run.install python requirements: 2.6e-05s
runem: │├pre-run.ls -alh runem: 0.004954s
runem: ├edit (total): 0.557559s
runem: │├edit.reformat py: 0.557559s
runem: ├analysis (total): 21.526145s
runem: │├analysis.pylint py: 7.457029s
runem: │├analysis.flake8 py: 0.693754s
runem: │├analysis.mypy py: 1.071956s
runem: │├analysis.pytest: 6.780303s
runem: │├analysis.json validate: 0.035359s
runem: │├analysis.yarn run spellCheck: 4.482992s
runem: │├analysis.prettier: 1.004752s
runem: report: coverage html: ./reports/coverage_python/index.html
runem: report: coverage cobertura: ./reports/coverage_python/cobertura.xml
runem: DONE: runem took: 8.820488s, saving you 13.268196s
```

### 6.2 Bar-graphs with `termplotlib``

If you have `termplotlib` installed you will see

```text
runem: Running 'pre-run' with 2 workers (of 8 max) processing 2 jobs
runem: Running 'edit' with 1 workers (of 8 max) processing 1 jobs
runem: Running 'analysis' with 7 workers (of 8 max) processing 7 jobs
runem: reports:
runem                                  [14.174612]  ███████████████▋
├runem.pre-build                       [ 0.025858]
├runem.run-phases                      [14.148587]  ███████████████▋
├pre-run (total)                       [ 0.005825]
│├pre-run.install python requirements  [ 0.000028]
│├pre-run.ls -alh runem                [ 0.005797]
├edit (total)                          [ 0.579153]  ▋
│├edit.reformat py                     [ 0.579153]  ▋
├analysis (total)                      [36.231034]  ████████████████████████████████████████
│├analysis.pylint py                   [12.738303]  ██████████████▏
│├analysis.flake8 py                   [ 0.798575]  ▉
│├analysis.mypy py                     [ 0.335984]  ▍
│├analysis.pytest                      [11.996717]  █████████████▎
│├analysis.json validate               [ 0.050847]
│├analysis.yarn run spellCheck         [ 8.809372]  █████████▊
│├analysis.prettier                    [ 1.501236]  █▋
runem: report: coverage html: ./reports/coverage_python/index.html
runem: report: coverage cobertura: ./reports/coverage_python/cobertura.xml
runem: DONE: runem took: 14.174612s, saving you 22.6414s
```

NOTE: each phase's total system-time is reported above the timing for the individual jobs ran in that phase. This is NOT wall-clock time.

## 7. Using Help to get an Overview of Your Jobs

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

## 8. Configuration

`runem` searches for `.runem.yml` and will pre-load the command-line options with

Configuration is Yaml and consists of two main configurations, `config` and `job`:

- `config` describes how the jobs should be run.
- each `job`  entry describe a job-task, such and running unit-tests, linting or running any other type of command.

### 8.1. `config` - Run 'em global config

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

### 8.2. `job` - Job config
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

## 9. Troubleshooting & Known issues

### 9.1 I don't see bar graph timing reports!
We don't specify it in the output to reduce dependency installation for ci/cd. We may change this decision, especially as `halo` is a first-order dependency now.

#### Solution:
install `termplotlib`, 

### 9.2 I can't specify a dependency!
Outside of `phases` we don't support direct dependency-chaining between tasks. We would like to do this at some point. PRs gladly accepted for this.

#### Solution
Use `phases` instead, or contribute a PR.

### 9.3 Why is there so much output on errors, it looks duplicated?
We haven't looked at how we manage exception-handling with the python `multiprocessing` library, yet. Errors in `multiprocessing` procs tend to be re-reported in the calling process. PRs welcome.

#### Solution
Just look at one of the outputs.

### 9.4 I can't see reports for job when errors happen!
We try to show reports for completed tasks. If the task you're interested in doesn't show it probably hasn't been executed yet. Otherwise scroll up and you should see the reports and timings of *completed* tasks, if not, you may need to increase your buffer size.

#### Solution
If you are focusing on one task and are only interested in how that task is performing/operating, use one of the many filtering options e.g. `--jobs "your job name" "another job name"`.

### 9.5 I want to see log output for tasks in real-time, as they're happening!
We don't stream stdout/stderr direct to console, or provide functionality for doing so, yet. Yes it would be a nice feature and we welcome PRs for it.

#### Solution
On failure and with `--verbose` mode, the exact command is logged to console along with the environment that job was run in. You can copy/paste that command line to a terminal and run the command manually. The stdout/stderr will then be as you would get for that command. Refer to the documentation for that command.

---
# Contributing to and supporting runem

[![codecov](https://codecov.io/gh/lursight/runem/branch/main/graph/badge.svg?token=run-test_token_here)](https://codecov.io/gh/lursight/runem)
[![CI](https://github.com/lursight/runem/actions/workflows/main.yml/badge.svg)](https://github.com/lursight/runem/actions/workflows/main.yml)

Awesome runem created by lursight

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Sponsor

[❤️ Sponsor this project](https://github.com/sponsors/lursight/)
