## Reports on your tasks

Runem has a built-in support for reporting on tasks

### Task timings report

Runem will run the task and report how long the task took and whether it saved you any time, for example:

```text
# output from runem when run on runem's project, without `termplotlib`
runem: Running 'pre-run' with 2 workers (of 8 max) processing 2 jobs
runem: Running 'edit' with 1 workers (of 8 max) processing 1 jobs
runem: Running 'analysis' with 7 workers (of 8 max) processing 7 jobs
runem: reports:
runem: runem: 8.820488s
runem: ├runem.pre-build: 0.019031s
runem: ├runem.run-phases: 8.801317s
runem: ├pre-run (user-time): 0.00498s
runem: │├pre-run.install python requirements: 2.6e-05s
runem: │├pre-run.ls -alh runem: 0.004954s
runem: ├edit (user-time): 0.557559s
runem: │├edit.reformat py: 0.557559s
runem: ├analysis (user-time): 21.526145s
runem: │├analysis.pylint py: 7.457029s
runem: │├analysis.flake8 py: 0.693754s
runem: │├analysis.mypy py: 1.071956s
runem: │├analysis.pytest: 6.780303s
runem: │├analysis.json validate: 0.035359s
runem: │├analysis.yarn run spellCheck: 4.482992s
runem: │├analysis.prettier: 1.004752s
runem: report: coverage html: ./reports/coverage_python/index.html
runem: report: coverage cobertura: ./reports/coverage_python/cobertura.xml
runem: DONE: runem took: 8.820488s, saving you 13.268196s
```

### Bar-graphs with `termplotlib`

If you have `termplotlib` installed you will see something like:

```text
runem: Running 'pre-run' with 2 workers (of 8 max) processing 2 jobs
runem: Running 'edit' with 1 workers (of 8 max) processing 1 jobs
runem: Running 'analysis' with 7 workers (of 8 max) processing 7 jobs
runem: reports:
runem                                  [14.174612]  ███████████████▋
├runem.pre-build                       [ 0.025858]
├runem.run-phases                      [14.148587]  ███████████████▋
├pre-run (user-time)                   [ 0.005825]
│├pre-run.install python requirements  [ 0.000028]
│├pre-run.ls -alh runem                [ 0.005797]
├edit (user-time)                      [ 0.579153]  ▋
│├edit.reformat py                     [ 0.579153]  ▋
├analysis (user-time)                  [36.231034]  ████████████████████████████████████████
│├analysis.pylint py                   [12.738303]  ██████████████▏
│├analysis.flake8 py                   [ 0.798575]  ▉
│├analysis.mypy py                     [ 0.335984]  ▍
│├analysis.pytest                      [11.996717]  █████████████▎
│├analysis.json validate               [ 0.050847]
│├analysis.yarn run spellCheck         [ 8.809372]  █████████▊
│├analysis.prettier                    [ 1.501236]  █▋
runem: report: coverage html: ./reports/coverage_python/index.html
runem: report: coverage cobertura: ./reports/coverage_python/cobertura.xml
runem: DONE: runem took: 14.174612s, saving you 22.6414s
```

NOTE: each phase's total system-time is reported above the timing for the individual jobs ran in that phase. This is NOT wall-clock time.

