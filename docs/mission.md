# Mission

## Reducing the wall-clock time running your developer-local tasks

`runem` (run 'em) is an unopinionated way to declare and run the many command-line tools developers use regularly.

## Core objective

The core objective of Runem is to minimize the wall-clock time required for
running checks, supporting
[shift-left testing](https://en.wikipedia.org/wiki/Shift-left_testing). Overall it is
designed to enhance iteration speed and boost developer productivity.

`runem` is also designed to be easy-to-learn and simple-to-use, but `runem`
also has many powerful tools for advanced users.

Job definitions are declarative and simple.

The in-built reports show how long each job took and how much time `runem` saved you.

Jobs can be filtered in or out very easily.

Multiple projects can be supported in a single `.runem.yml` config, supporting
workspaces and mono-repos. Also multiple task types, working on multiple
file-types can be supported.

Finally, because of how it's built, job definitions are auto-documented via
`runem --help`. This help onboarding new developers by making tool-discovery
easier. Therefore it also helps maintenance of developer tools.

## Why is it called `runem`?

Primarily `runem`, as a command line tool, is quick to type and tries to just
get out of the way when running your developer-local tools.

The name "runem" is a portmanteau of "run" and "them", encapsulating that runem
"runs them", but slightly faster.
