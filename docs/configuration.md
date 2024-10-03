# Configuration

`runem` searches for `.runem.yml` and will pre-load the command-line options with

Configuration is Yaml and consists of two main configurations, `config` and `job`:

- `config` describes how the jobs should be run.
- each `job`  entry describe a job-task, such and running unit-tests, linting or running any other type of command.

## `config` - Run 'em global config

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

## `job` - Job config
- **job:**
  - *Description:* Represents a specific job task that is to be run asynchronously.
  - *Fields:*
    - **command:**
      - *Description:* a simple command line to be run. Commands will be run by the system exactly as they are written. Use `addr` for more complicated jobs. Commands are run in their associate `context`.
      - *Example:
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

    - **addr:**
      - *Description:* Specifies where a python function can be found. The python function will be loaded at runtime by `runem` and called with the `context`. The function receives all information needed to run the job, including `label`, `JobConfig`, `verbose`, `options` and other run-time context.
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
