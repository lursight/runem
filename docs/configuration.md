# Configuration file

Valid configuration filepaths:
- `.runem.yml` in the root of the project

`runem` searches up the directory tree for a `.runem.yml` file, stopping at the first one it finds.

The path to the `.runem.yml` is used to determine the base/root cwd path for running job-tasks. You can override this on a per-job basis.

The `.runem.yml` configuration file is Yaml and consists of two main configuration sections, a single `config` entry and one or more `job` entries:

- `config`: describes _how_ `runem` should run the jobs.
    - There is a single global config entry, describing how `runem` should run the jobs.
- `job`: one or more `job` entries.
    - each describing a "job-task", for example:
        - deps install
        - workspace config
        - unit-tests
        - linting
        - code coverage
        - any other type of command.

## `config` - runem's global project settings

### config.phases
Specifies the different phases of the testing process, in the order they are to be run. Each job will be run under a specific phase.

**Values:** A list of strings representing "phases" such as pre-run (e.g. bootstrapping), edit (running py-black or prettifier or clang-tools), and analysis (unit-tests, coverage, linting).

**Example**:
```yaml
phases:
- pre-run
- edit
- analysis
```

### config.files
Defines filters for categorizing files based on tags and regular expressions. Maps tags to files-to-be tested. If a job has one or more tags that map to file-filters that job will receive all files that match those filters.

**Values:** A list of dictionaries, each containing a 'filter' key with 'tag' and 'regex' subkeys.

### config.options:
Configures various option-overrides for the job-tasks. Overrides can be set on the command line and accessed by jobs to turn on or off features such as 'check-only' or to opt out of sub-tasks.

**Values:** A list of dictionaries, each containing 
- 'option' key with 'default' boolean value
- a 'name'
- a 'type'
- a 'desc'
- an optional 'alias'

NOTE: only 'bool' types are currently supported.

### config.options.default:** Specifies the default value of the option.
- **name:** A string for the name of the option.
- **type:** Indicates the data type of the option (e.g., bool for boolean) NOTE: only `boolean` is currently supported.
- **desc:** A human-readable/friendly description of the option and its intended use cases.
- **alias:** (Optional) Provides an alias for the option's name if specified. 

## `job` - Job config
*Description:* Represents a specific job task that is to be run asynchronously.

*Fields:*

- TODO

*Example:*
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
```
### job.command
*Description:* A simple command line to be run. Commands will be run by the system exactly as they are written. Use `addr` or `module` for more complicated jobs. Commands are run in their associate `context`.

*Examples*:
```yaml
command: yarn run pretty
```
```yaml
command: python3 -m pylint **/*.py
```
```yaml
command: bash scripts/build_wrapper.sh
```
```yaml
command: clang-tidy -checks='*' -fix -header-filter='.*' your_file.cpp
```
### job.module
```yml
module: python.import.dot.notation.file_name.runem_function
```
A fully qualified python-import-path to a runem function - see below for an example of a Job Function.

Similar to `addr`, "module" imports the function at the given location. Whilst `addr` uses a filepath and a function name, `module` uses a python dot-notation path to import a function. That function is then, at execution time, called with the context's `kwargs` - see below for an example of a Job Function.

`.runem.yml` file-path and that is used for the `cwd`, **not** the cwd parameter in the config (PRs welcome). context for the import, and the PYTHONPATH will be used. The function receives all information needed to run the job, including `label`, `JobConfig`, `verbose`, `options` and other run-time context.

**Example:**

```yaml
module: scripts.test_hooks.fastlane.run_fastlane_build
```

#### Gotchas and Troubleshooting `job.module`
##### Virtual env
`module` jobs (at time of writing) inherit the `runem` env (virtual or otherwise). This means that the `runem` env needs to have the dependencies required by the job whenever runem is run, which can lead to problems in ci/cd envs with minimal installs.

##### Import path context
`module` jobs uses python's inbuilt `importlib` to grab and validate the import-path.

This mean that standard python import rules apply. Consider that: 

- any `PYTHONPATH`, `PATH`, `sys.path` dirs will be respected by the python runtime that is running `runem`.
- for module-path `path.to.job.func`, you would expect the `.runem.yml` to be next to the `path/` directory.
- for module-path `dir1.dir2.job_file.func` there should be `__init__.py` files in each of the directories in that path i.e. `dir1/__init__.py` and `dir2/__init__.py`.
- executing `runem` from the common root path, that is, the path that `.runem.yml` is in.

It is easiest to think of the import root as being relative to the PWD when running runem, so jobs that use `module` may break when running `runem` from other subdirs in the directory tree.

##### Verifying `module` address is correct
If `python3 -c "import my.module.runem_func"` works then `module: my.module.runem_func` _should_ also work.

### job.addr:
Specifies where a stand-alone python function can be found by `runem`.

This can be a more stable version of `job.module`, depending on use-case.

The address is a combination of `file` (path) and `function` (name), pointing at a callable-like object/function - see below for an example of a Job Function.

The python function will be loaded at runtime by `runem` and called with the `context`.

The function receives all information needed to run the job, including `label`, `JobConfig`, `verbose`, `options` and other run-time context.


*Sub keys:*

- **file:**
    - The file-path of the python fie containing `function`
    - When relative, is relative to the `.runem.yml` config file.
- **function:**:
    - The function-name within `file`.
    - See below for details on the context the function should accept and why.


*Example:*
```yaml
addr:
    file: scripts/test-hooks/rust_wrappers.py
    function: _job_rust_code_reformat
```

#### Gotchas with `job.addr`
Imports to other python files may not work as the function is not "imported" in the normal sense, rather it is "loaded" as an independent callable entity, albeit inside of the `runem` environment. If you're expecting to be able to do import other project python modules from your runem job, and you are getting import-errors, consider using `job.module` instead.

### job.ctx:
*Description:* Provides the *execution* context for the job, including the working directory and parameters. Not to be confused with the kwargs context that the job is actually passed. The `job.ctx` describe to `runem` how the job should be run, on what `cwd` path and with which files, etc.

*Subkeys:*
- **cwd:** Specifies the working directory for the job.
- **params:** Specifies parameters for the job.

*Example:*
```yaml
cwd: .
params:
  limitFilesToGroup: true
```

### job.label:
Assigns a label to the job for identification.

*Example:*
```yaml
label: reformat py
```

### job.when:
*Description:* Defines the conditions under which the job should run.

*Subkeys:*

- **phase:** Specifies the testing phase in which the job should run.
- **tags:** Specifies the tags associated with the job.

*Example:*
```yaml
when:
  phase: edit
  tags:
    - py
    - format
```

## Job Functions
All python `runem_function` callables must accept `kwargs`. This is so that they can call sub-procs with an inherited context.
### Untyped job functions
```py
def _runem_function(**kwargs) -> None:
    """Simple un-typed, runem func to orchestrate a task."""
    pass
```

### Typed job functions
```py
from typing_extensions import Unpack  # for python 3.9 back-compat
from runem.types import JobKwargs


def _runem_function(
    **kwargs: Unpack[JobKwargs],
) -> None:
    """Typed runem func with inspectable context kwargs."""
    pass
```
