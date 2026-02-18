# Hooks

Hooks allow custom callbacks to be called when events trigger.

## Hook configuration

Hooks are essentially a simple `job`.

Hooks have:

- a callable, either a simple `command` or a python function `addr`.
- an event-bind `hook_name`

## Available hooks

Currently we only support `on-exit` hooks.

## on-exit

`on-exit` hooks are called when runem has completed, irrespective of the pass/fail
status.

### Context for command-based hooks

Hook entries that use `command:` (instead of `addr`) can use the **`{runem_ctx}`**
placeholder in the command string. It is replaced at run time with a single shell-safe
JSON argument containing run context, e.g.:

- **`root_dir`** — project root path (directory containing `.runem.yml`).
- **`run_success`** — `true`/`false`; whether the run completed without job failure
  (on-exit only).
- **`wall_clock_time_saved`** — seconds (number); wall-clock time saved by
  parallelisation (on-exit only).

Example: `command: echo {runem_ctx}` becomes something like
`echo '{"root_dir":"/path/to/repo","run_success":true,"wall_clock_time_saved":12.5}'`.
You can pipe the output to `jq` or parse it in a script.

### Context passed to on-exit hooks (Python)

Python hooks (using `addr`) receive the usual job kwargs plus hook-specific context:

- **`root_dir`** — project root (directory containing `.runem.yml`). Use this for paths
  under the repo.
- **`run_success`** — `True` if all jobs completed without failure, `False` otherwise.
- **`wall_clock_time_saved`** — `time delta` of wall-clock time saved by
  parallelisation.

They also receive the common kwargs (`config_metadata`, `root_path`, `label`, `options`,
`procs`, `verbose`). See `HookKwargs` / `HookSpecificKwargs` in the codebase for the
full signature.

### `on-exit` examples

#### Example OSX text-to-speech

```yml
- hook:
    hook_name: on-exit
    command: "say done"

    ON_EXIT = "on-exit"
```

#### Example OSX notification

```yml
- hook:
    hook_name: on-exit
    command: osascript -e 'display notification "runem has completed running" with title "Runem"'

    ON_EXIT = "on-exit"
```
