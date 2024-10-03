# Quick-start

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

## A more complete quick-start

Here's a simple setup for a python project.

### A simple `.runem.yml`

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
          name: check-only
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

### A simple python task

Here's a simple python file describing a job. This accompanies the above `.runem.yml`.

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
    if options["check-only"]:
        extra_args.append("--check")
        docformatter_extra_args = []  # --inplace is not compatible with --check

    if options["black"]:
        black_cmd = [
            "python3",
            "-m",
            "black",
            *extra_args,
            *python_files,
        ]
        kwargs["label"] = f"{label} black"
        run_command(cmd=black_cmd, **kwargs)

    if options["docformatter"]:
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
        if options["check-only"]:
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
The above python file accompanies the above `.runem.yml` configuration and does slightly more advanced work. The file contains:
- a single job.
- the job itself linearises edit tasks that would otherwise contend for write-access to the files they operate on.
  - formatting and doc-generation both edit files, conforming them to the coding standard.
- uses `options` (see the config section) to control whether to:
  - use `check-only` mode for CiCd, modifying the command-line switched passed down to the sub-commands.
  - control whether `python-black` and/or/nor `docformatter` is run.
- modifies the allowed-exit codes for `docformatter` to be `0` or `3`, matching the designed behaviour of that tool.
