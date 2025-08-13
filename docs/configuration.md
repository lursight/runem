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

### job.addr:
*Description:* Specifies where a python function can be found. The python function will be loaded at runtime by `runem` and called with the `context`. The function receives all information needed to run the job, including `label`, `JobConfig`, `verbose`, `options` and other run-time context.

*Subkeys:*
- **file:** Indicates the file path of the job.
- **function:** Indicates the function within the file that represents the job.

*Example:*
```yaml
addr:
    file: scripts/test-hooks/rust_wrappers.py
    function: _job_rust_code_reformat
```


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

