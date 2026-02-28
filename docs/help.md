# Job manifest
Using `--help`` to get an overview of your Jobs

The `--help` switch will show you a full list of all the configured job-tasks, the tags, and the override options. `--help` describes how to configure a specific run for *your* `.runem.yml` setup, and does NOT just document `runem` itself; it documents *your* workflow.

```bash
$ python -m runem --help
# or
$ runem  --help
```
```
usage: runem.py [-h] [--jobs JOBS [JOBS ...]] [--not-jobs JOBS_EXCLUDED [JOBS_EXCLUDED ...]] [--phases PHASES [PHASES ...]]
                [--not-phases PHASES_EXCLUDED [PHASES_EXCLUDED ...]] [--tags TAGS [TAGS ...]] [--not-tags TAGS_EXCLUDED [TAGS_EXCLUDED ...]]
                [--black] [--no-black] [--check-only] [--no-check-only] [--coverage] [--no-coverage] [--docformatter] [--no-docformatter]
                [--generate-call-graphs] [--no-generate-call-graphs] [--install-deps] [--no-install-deps] [--isort] [--no-isort] [--profile]
                [--no-profile] [--unit-test] [--no-unit-test]
                [--call-graphs | --no-call-graphs]
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
  --unit-test           run unit tests
  --no-unit-test        turn off run unit tests
```

## Shell tab completion (bash, zsh, fish)

`runem` supports shell completion through the optional (`argcomplete`)[https://pypi.org/project/argcomplete/] dependency.

The parser provides completion values for project-specific `--[not-]jobs`, `--[not-]tags`, and `--[not-]phases`.

Install with completion support:
```bash
pip install -e ".[completion]"
# or for a normal install:
pip install "runem[completion]"
```

Enable completion:
```bash
# bash
eval "$(register-python-argcomplete runem)"

# zsh
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete runem)"

# fish
register-python-argcomplete --shell fish runem | source
```

### Completion mechanism
`runem` supports `argcomplete` via its inbuilt completion mode.

This is why completions can include your real job names/tags/phases from `.runem.yml`.

