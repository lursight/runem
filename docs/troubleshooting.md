# Troubleshooting & Known issues

## I don't see bar graph timing reports!
We don't specify it in the output to reduce dependency installation for ci/cd. We may change this decision, especially as `halo` is a first-order dependency now.

### Solution:
install `termplotlib`

```sh
python3 -m pip install termplotlib
```

## I can't specify a dependency!
Outside of `phases` we don't, yet, support direct dependency-chaining between tasks. We would like to do this at some point. PRs gladly accepted for this.

### Solution
Use `phases` instead, or contribute a PR.

## When errors happen I don't see reports for jobs!
We try to show reports for completed tasks. If the task you're interested in doesn't show, it probably hasn't been executed yet.

### Solution
Otherwise scroll up and you should see the reports and timings of *completed* tasks, if not, you may need to increase your terminal's view-buffer size, or apply a filter to focus on that job.

If you are focusing on one task and are only interested in how that task is performing/operating, use one of the many filtering options e.g. `--jobs "your job name" "another job name"` or `--tags unittest`.

## I want to see log output for tasks in real-time, as they're happening!

### Solution
Use `--verbose` mode.
