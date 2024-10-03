# Troubleshooting & Known issues

## I don't see bar graph timing reports!
We don't specify it in the output to reduce dependency installation for ci/cd. We may change this decision, especially as `halo` is a first-order dependency now.

### Solution:
install `termplotlib`,

## I can't specify a dependency!
Outside of `phases` we don't support direct dependency-chaining between tasks. We would like to do this at some point. PRs gladly accepted for this.

### Solution
Use `phases` instead, or contribute a PR.

## Why is there so much output on errors, it looks duplicated?
We haven't looked at how we manage exception-handling with the python `multiprocessing` library, yet. Errors in `multiprocessing` procs tend to be re-reported in the calling process. PRs welcome.

### Solution
Just look at one of the outputs.

## When errors happen I don't see reports for jobs!
We try to show reports for completed tasks. If the task you're interested in doesn't show, it probably hasn't been executed yet. Otherwise scroll up and you should see the reports and timings of *completed* tasks, if not, you may need to increase your terminal's view-buffer size.

### Solution
If you are focusing on one task and are only interested in how that task is performing/operating, use one of the many filtering options e.g. `--jobs "your job name" "another job name"` or `--tags unittest`.

## I want to see log output for tasks in real-time, as they're happening!
We don't stream stdout/stderr direct to console, or provide functionality for doing so, yet. However, we also believe that it would be a nice feature and welcome PRs.

### Solution
On failure and with `--verbose` mode, the exact command is logged to console along with the environment that job was run in. You can copy/paste that command line to a terminal and run the command manually. The stdout/stderr will then be as you would get for that command. Refer to the documentation for that command.
