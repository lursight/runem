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
`on-exit` hooks are called when runem has completed, irrespective of the pass/fail status.

### `on-exit` examples:
#### Example OSX text-to-speach:
```yml
- hook:
    hook_name: on-exit
    command: "say done"

    ON_EXIT = "on-exit"
```
#### Example OSX notification:
```yml
- hook:
    hook_name: on-exit
    command: osascript -e 'display notification "runem has completed running" with title "Runem"'

    ON_EXIT = "on-exit"
```
