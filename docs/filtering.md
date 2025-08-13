# Filtering jobs
`runem` is a command-line tool designed to run dev-ops tasks as fast as possible.

The CLI is designed with two goals in mind:

- easy job filtering, allowing focus on problems and fast-iteration.
- better job-discovery and on boarding - helping teams to stay on top of the sometimes complicated devops infrastructure and tooling of a project. (see the help section)
```bash
# run all configured default jobs
runem

# ---- or ----

# apply filters and controls
runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
      [--phases phaseX, phaseY] \
      [--MY-OPTION] [--not-MY-OPTION]

# ---- or ----

# run as a module
python3 -m runem [--tags tag1,tag2,tag3] [--not-tags tag1,tag2,tag3] \
                 [--phases phaseX, phaseY] \
                 [--MY-OPTION] [--not-MY-OPTION]
```

## Filtering by Tag
Jobs are tagged in the .runem.yml config file. Each unique tags is made available on the command-line. To see which tags are available use `--help`. To add a new tag extend the `tags` field in the `job` config.

You can control which types of jobs to run via tags. Just tag the job in the config and then from the command-line you can add `--tags` or `--not-tags` to refine exactly which jobs will be run.

To debug why a job is not selected pass `--verbose`.

For example, if you have a `python` tagged job or jobs, to run only run those jobs you would do the following:

```bash
runem --tags python
```

`--tags` are exclusive filter in, that is the tags passed in replace are the only tags that are run. This allows one to focus on running just a subset of tags.

`--not-tags` are subtractive filter out, that is any job with these tags are not run, even if they have tags set via the `--tags` switch. Meaning you can choose to run `python` tagged job but not run the `lint` jobs with `--tags python --not-tags lint`, and so on.

### Run jobs only with the 'lint' tag:

```bash
runem --tags lint
```

### If you want to lint all code _except_ nodejs code (and you have the appropriate tags):

```bash
runem --tags lint --not-tags deprecated
```

### Run fast checks on `pre-commit`

If you have fast jobs that tagged as appropriate for pre-commit hooks.

```bash
mkdir scripts/git-hooks
echo "runem --tags pre-commit" > scripts/git-hooks/pre-commit
# add the following to .git/config
# [core]
#   # ... existing config ...
#	  hooksPath = ./scripts/git-hooks/husky/
```

## Filtering by Phase

Sometimes just want to run a specific phase, so you can focus on it and iterate quickly, within that context.

### Focus on a phase

For example, if you have a `reformat` phase, you might want to run just `reformat` jobs phase whilst preparing a commit and are just preparing cosmetic changes e.g. updating comments, syntax, or docs.

```bash
runem --phase reformat
```

### Exclude slow phases temporarily

If you have 4 stages `bootstrap`, `pre-run`, `reformat`, `test` and `verify` phase, and are tightly iterating and focusing on the 'test-coverage' aspect of the test-phase, then you do not care about formatting as long as you can see your coverage results ASAP. However if your test-coverage starts passing then you will care about subsequent stages, so you can exclude the slower reformat-stage with the following and everything else will run.

```bash
runem --not-phase pre-run reformat
```

**Note:** The `--tags` and `--not-tags` options can be used in combination to further refine task execution based on your requirements.
