Changelog
=========


(unreleased)
------------
- Merge pull request #63 from
  lursight/dependabot/github_actions/actions/cache-4. [Frank Harrison]

  chore(deps): bump actions/cache from 3 to 4
- Chore(deps): bump actions/cache from 3 to 4. [dependabot[bot]]

  Bumps [actions/cache](https://github.com/actions/cache) from 3 to 4.
  - [Release notes](https://github.com/actions/cache/releases)
  - [Changelog](https://github.com/actions/cache/blob/main/RELEASES.md)
  - [Commits](https://github.com/actions/cache/compare/v3...v4)

  ---
  updated-dependencies:
  - dependency-name: actions/cache
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- Feat(simple-files): adds ability to pass file-lists to simple-
  commands. [Frank Harrison]
- Feat(simple-files): strongly types the simple job executor. [Frank
  Harrison]
- Feat(simple-files): fixes docstring. [Frank Harrison]


0.1.2 (2024-11-18)
------------------
- Release: version 0.1.2 🚀 [Frank Harrison]
- Chore(actions): simplifies code paths for actions. [Frank Harrison]
- Chore(contrib): removes the Makefile commands that have been removed.
  [Frank Harrison]

  .. this should have been in the last PR.
- Chore(contrib): update the CONTRIBUTING docs and removes defunct
  scripts from Makefile. [Frank Harrison]
- Chore(faster-actions): removes redundant github actions. [Frank
  Harrison]

  This should speed up github actions, but it may lead to more false-positives as we are relying on runem to be working and realiabel to run our own checks....

  This could come back to bite us.
- Chore(extra-ctx): adds config_metadata to job kw-args. [Frank
  Harrison]

  This allows much greater depth of testing based on other jobs-inclusion and metadata.
- Chore(extra-ctx): moves the job-task calling to use kwargs explicitly.
  [Frank Harrison]
- Chore(extra-ctx): sort kwargs passed to jobs. [Frank Harrison]
- Merge pull request #59 from lursight/chore/cleaner_type_exports.
  [Frank Harrison]

  Chore/cleaner type exports
- Chore(clean-types): fixes false-negative from 'isort --check' [Frank
  Harrison]
- Chore(clean-types): makes the public_api the actual exported api of
  the types module. [Frank Harrison]

  I think this could be better
- Chore(clean-types): renames type_wip -> types. [Frank Harrison]
- Chore(clean-types): fixes up more of the test-hooks (badly named) for
  runem itself. [Frank Harrison]
- Chore(clean-types): splits out the rest of the types. [Frank Harrison]
- Chore(clean-types): moves config and serialisationtypes to own file.
  [Frank Harrison]
- Chore(clean-types): moves error into new errors.py types file. [Frank
  Harrison]
- Chore(clean-types): starts moving some types into 'common' [Frank
  Harrison]
- Chore(clean-types): moves the types into types/wip whilst I work out
  the public API. [Frank Harrison]
- Chore(clean-types): splits out the job and hook execution types, ahead
  of building a better public api for type exports. [Frank Harrison]
- Chore(clean-types): sorts the job kwargs. [Frank Harrison]


0.1.1 (2024-11-17)
------------------
- Release: version 0.1.1 🚀 [Frank Harrison]
- Merge pull request #58 from lursight/fix/completed_job_counts. [Frank
  Harrison]

  fix(complete-job-count): fixes and simplifies the in-progress report code
- Fix(complete-job-count): fixes and simplifies the in-progress report
  code. [Frank Harrison]

  The core problem was that the remaining-job-count didn't match the
  number of job-labels that were being shown.

  The root-cause was due to some of the job-tasks completing before the
  `_update_progress()` thread had started monitoring the jobs.

  We fix this by adding a new parameter to the job-executer that tracks
  when job completed. It's a very simple fix and reduces the overall
  complexity for about the same cost of threading-primitives.


0.1.0 (2024-11-17)
------------------
- Release: version 0.1.0 🚀 [Frank Harrison]
- Merge pull request #57 from lursight/feat/replace_halo_with_rich.
  [Frank Harrison]

  feat(rich): moves to using rich instead of halo for spinners
- Feat(rich): moves to using rich instead of halo for spinners. [Frank
  Harrison]
- Merge pull request #56 from lursight/feat/better_job_function_typing.
  [Frank Harrison]

  feat(better-job-function-typing): adds stronger typing for job and hook tasks
- Feat(better-job-function-typing): adds stronger typing for job and
  hook tasks. [Frank Harrison]

  We do this by typing the kwargs convenience variable, for which we need
  to use `Unpack` (for back compatibility), and `type_extensions` for
  cross-python-version compatibility (i.e. something that work for all
  targeted version of python).

  As a side-effect of this we get the benefit of seeing when and where we
  add extra data into the call-stack for `job_execute()` and it emerges
  that we only extend the key-word args when we are calling hooks in a
  non-threaded way, which makes sense.

  We do several things to achieve this:
    1. We have common parameters passed to both hooks and job-tasks
        - These common parameters make the hooks and job-task feel similar
          to develop.
    2. We put all hook-specific kwargs in one place, and mark each as
       optional.
        - this, for now, is mainly because we only have one hook, so this
          will likely change.
    3. We share and combine kwargs in a range of inheritance types, mainly
       to work with(/around?) python-typing, which isn't great in this
       type of situation.
- Chore(ignores): adds the tox/ dir to the ignores. [Frank Harrison]
- Chore(ignores): update git ignore for coverage files and docs gen.
  [Frank Harrison]

  The docs are recent additions.
- Merge pull request #55 from lursight/chore/test_improvements. [Frank
  Harrison]

  Chore/test improvements
- Chore(coverage): reduce false-positives by deleteing old
  coverage_report files. [Frank Harrison]

  Sometimes we would have stale .coverage_report.* files left behind where
  from the multi-distributed pytest runs. These would lead more lines
  being reported as coverage than actual - aka false-positive test passes
  for coverage.
- Chore(help-tests): fixes the help output width in tests. [Frank
  Harrison]

  This reduces false-negative test results where we get word-splits in
  directories or between process counters or other dynamic content.

  This was due to the width of the terminal when the test was being run
  being variant with developer-machine. This uses a fixed-width output,
  reducing, if not stopping issues.
- Chore(deps): updates black 24.3.0 -> 24.10.0. [Frank Harrison]
- Chore(deps): updates to latest pytest 8.1.1 -> 8.3.3 + plugins. [Frank
  Harrison]


0.0.32 (2024-11-17)
-------------------
- Release: version 0.0.32 🚀 [Frank Harrison]
- Merge pull request #54 from lursight/chore/use_tox_on_release. [Frank
  Harrison]

  chore(release): use tox on 'make release'
- Chore(release): use tox on 'make release' [Frank Harrison]

  This will run the checks across all versions, hopefully making
  everything more solid.
- Merge pull request #53 from lursight/dependabot/npm_and_yarn/cross-
  spawn-7.0.5. [Frank Harrison]

  chore(deps): bump cross-spawn from 7.0.3 to 7.0.5
- Chore(deps): bump cross-spawn from 7.0.3 to 7.0.5. [dependabot[bot]]

  Bumps [cross-spawn](https://github.com/moxystudio/node-cross-spawn) from 7.0.3 to 7.0.5.
  - [Changelog](https://github.com/moxystudio/node-cross-spawn/blob/master/CHANGELOG.md)
  - [Commits](https://github.com/moxystudio/node-cross-spawn/compare/v7.0.3...v7.0.5)

  ---
  updated-dependencies:
  - dependency-name: cross-spawn
    dependency-type: indirect
  ...
- Merge pull request #49 from
  lursight/feat/allow_additional_files_to_be_checked. [Frank Harrison]

  Feat/allow additional files to be checked
- Feat(file-controls): adds way to get files changed between branches.
  [Frank Harrison]

  This is useful if we want to do quick checks only on code that has
  changed since 'main' when pushing, or on a sibling branch or similar.

  For example, if we are using `--exec` in a rebase, we can start running
  check half-way through the list of commits, instead of every commit, but
  have the code check all files that have changes - meaning we can see the
  impact of changes throughout the branch, without working on *every*
  commit - sometimes this is very useful.
- Feat(file-controls): adds --always-files switch to force files to be
  checked. [Frank Harrison]

  Because of how we apply filters, filters for the files are applied
  before they're passed to the relevant jobs.

  This means that runem can now always check a subset of files, even if
  they're not in the HEAD or staged files, meaning we can verify if some
  files that we care about for a rebase or similar are copecetic.
- Merge pull request #52 from lursight/chore/pre-push_checks. [Frank
  Harrison]

  Chore/pre push checks
- Chore(tox): adds tox to run against multiple version of python on pre-
  push. [Frank Harrison]
- Chore(pre-push-checks): adds a clean-checkout pre-push git hook.
  [Frank Harrison]
- Chore(pre-push-checks): renames setup.py extras test -> tests. [Frank
  Harrison]
- Chore(pre-push-checks): adds option to get the root-path from the cli.
  [Frank Harrison]

  This will support pre-push hooks amongst other things, replacing
  ENV-variable that other projects I work on use.
- Chore(help-tests): fixes the tests when dirs are long. [Frank
  Harrison]

  If the dir-path was too long it would wrap and we could do a simple replace on it.
- Chore(help-tests): shows the failing output when the help comparrisons
  fail. [Frank Harrison]
- Chore(help-tests): stops the help files being overwritten
  unexpectedly. [Frank Harrison]
- Chore(typo): fixes argsparse -> argparse. [Frank Harrison]
- Chore(tox): runs checks against multiple targets of python using tox.
  [Frank Harrison]
- Chore(yarn): unconditionally installs yarn deps, at least once, in
  clean checkouts. [Frank Harrison]

  Reminder that we use yarn because it's simpler and better for
  spell-checking and git-hooks, mainly because the hooks get
  auto-installed when the yarn deps are installed.
- Chore(pretty): updates docs config file missed formatting after
  pervious PR. [Frank Harrison]
- Merge pull request #51 from lursight/chore/docs. [Frank Harrison]

  Chore/docs
- Chore(better-docs): make links in README.md absolute to docs. [Frank
  Harrison]
- Chore(better-docs): change label in docs badge to emoticon. [Frank
  Harrison]
- Chore(better-docs): adds docs badge and moves others to top. [Frank
  Harrison]
- Chore(better-docs): rewrites and restructures the docs. [Frank
  Harrison]

  We split README into multiple mark-down files in docs/ allowing github
  pages to publish them via Jekyll.
- Chore(better-docs): configures Jekyll theme ahead of publish docs as
  pages. [Frank Harrison]

  We configure the docs in the root-dir so that the index of the Docs site
  is the same-same as the README.md at the root of the checkout.
- Merge pull request #50 from
  lursight/dependabot/npm_and_yarn/micromatch-4.0.8. [Frank Harrison]

  chore(deps): bump micromatch from 4.0.5 to 4.0.8
- Chore(deps): bump micromatch from 4.0.5 to 4.0.8. [dependabot[bot]]

  Bumps [micromatch](https://github.com/micromatch/micromatch) from 4.0.5 to 4.0.8.
  - [Release notes](https://github.com/micromatch/micromatch/releases)
  - [Changelog](https://github.com/micromatch/micromatch/blob/master/CHANGELOG.md)
  - [Commits](https://github.com/micromatch/micromatch/compare/4.0.5...4.0.8)

  ---
  updated-dependencies:
  - dependency-name: micromatch
    dependency-type: indirect
  ...


0.0.31 (2024-04-20)
-------------------
- Release: version 0.0.31 🚀 [Frank Harrison]
- Merge pull request #48 from
  lursight/feat/merge_head_and_modified_files_in_git. [Frank Harrison]

  feat(git-files): allows head, staged and unstaged git files
- Feat(git-files): allows head, staged and unstaged git files. [Frank
  Harrison]

  This means we can run fast tests against all files that have recently changed and get better results.


0.0.30 (2024-04-13)
-------------------
- Release: version 0.0.30 🚀 [Frank Harrison]
- Merge pull request #47 from lursight/feat/git-fast-files. [Frank
  Harrison]

  Feat/git fast files
- Feat(git-files): adds -f and -h for handling changed files and head
  files. [Frank Harrison]

  This makes using runem for big projects MUCH more effecient.
- Chore(help): moves help switch from -h -> -H. [Frank Harrison]

  This is so we can add `-h` as `HEAD files`
- Chore(error-reporting): adds warn() and error() logging types. [Frank
  Harrison]
- Merge pull request #46 from lursight/chore/docs. [Frank Harrison]

  Chore/docs
- Chore(test): adds a new e2e test for tags-to-ignore. [Frank Harrison]

  Once again everything seems to be behaving properly.
- Chore(docs): annotates the tags-to-exclude test. [Frank Harrison]

  I thought it was buggy, but we have another issue somewhere.
- Chore(docs): updates the core-goal in the README. [Frank Harrison]
- Chore(test): adds NUM CORES handling to tests. [Frank Harrison]
- Chore(coverage): fixes coverage warnings. [Frank Harrison]
- Merge pull request #45 from lursight/chore/update_deps. [Frank
  Harrison]

  updates deps
- Updates deps. [Frank Harrison]
- Merge pull request #44 from lursight/chore/update_py_black. [Frank
  Harrison]

  Chore/update py black
- Chore(black): updates formatting after upgrading black. [Frank
  Harrison]
- Chore(deps): upgrades py-black following dependabot. [Frank Harrison]
- Merge pull request #43 from lursight/feat/user-local-hook_1st_pass.
  [Frank Harrison]

  Feat/user local hooks (1st pass)
- Feat(user-local-cfg): fixes for python 3.9 tests. [Frank Harrison]
- Feat(user-local-cfg): handles situations where jobs are in local
  configs. [Frank Harrison]

  ... and phases are missing.
- Chore(docs): stop the help-text test being verbose. [Frank Harrison]

  ... it is unlikely that --help will be used in verbose mode... probs. Sigh.
- Feat(user-local-cfg): gets user- and local- configs working. [Frank
  Harrison]
- Feat(user-local-cfg): splits the project loading into load and parse
  phases. [Frank Harrison]

  This is so we can use it to load user configs
- Feat(user-local-cfg): splits the config loading and the ConfigMetadata
  construction functions. [Frank Harrison]

  This allows re-using the parsing function for N files
- Feat(hooks): adds a hook system with support for ON_EXIT. [Frank
  Harrison]

  - we remove the deprecated function-type for jobs
  - we add support for hooks
  - add a hooks section to the .runem.yml reader
  - add a on-exit hook to the runem project's .runem.yml
- Merge pull request #42 from lursight/feat/prettier_tree_graph. [Frank
  Harrison]

  Feat/prettier tree graph
- Feat(prettier-tree-report): changes how we index the leaver on the
  report-tree. [Frank Harrison]

  Basically removes the duplicate information, reducing visual noise,
  especially after adding the variously shaded bar-graphs
- Chore(.runem): uses current best practise for accessing options in
  runem's own jobs. [Frank Harrison]
- Chore(.runem): connects the unit-test option to the runem python
  checks. [Frank Harrison]
- Chore(.runem): removes defunct options. [Frank Harrison]

  These were left over from lursight's config
- Chore(.runem): rename switches for consistency. [Frank Harrison]
- Fix(pretty-tree): adds extra test for bar-graph chars. [Frank
  Harrison]
- Chore: typo. [Frank Harrison]
- Merge pull request #41 from lursight/feat/prettier_tree_graph. [Frank
  Harrison]

  Feat/prettier tree graph
- Feat(tree-graph): hangs all tree leaves off of the runem.phases.
  [Frank Harrison]
- Feat(tree-graph): adds runem-reports regression checks. [Frank
  Harrison]

  This means we can capture any changes if they happen to the layout of
  the graph, as I intended to changed the layout next.
- Merge pull request #38 from
  lursight/dependabot/github_actions/softprops/action-gh-release-2.
  [Frank Harrison]

  chore(deps): bump softprops/action-gh-release from 1 to 2
- Chore(deps): bump softprops/action-gh-release from 1 to 2.
  [dependabot[bot]]

  Bumps [softprops/action-gh-release](https://github.com/softprops/action-gh-release) from 1 to 2.
  - [Release notes](https://github.com/softprops/action-gh-release/releases)
  - [Changelog](https://github.com/softprops/action-gh-release/blob/master/CHANGELOG.md)
  - [Commits](https://github.com/softprops/action-gh-release/compare/v1...v2)

  ---
  updated-dependencies:
  - dependency-name: softprops/action-gh-release
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...


0.0.29 (2024-03-18)
-------------------
- Release: version 0.0.29 🚀 [Frank Harrison]
- Merge pull request #40 from lursight/fix/time_saved. [Frank Harrison]

  Fix/time saved
- Feat(prettier-bars): clarifies that total is user-space time. [Frank
  Harrison]

  ... not wall-clock or system-time
- Feat(prettier-bars): distiguishes the wall-clock bars. [Frank
  Harrison]

  ... from the total/sum and sub-job bars, so that it's slightly easier to
  see where the time is being really spent.
- Fix(time-saved): clarifies which measurement is the wall-clock time
  for the entire run. [Frank Harrison]
- Fix(time-saved): add message about how long we _would_ have waited
  without runem. [Frank Harrison]
- Fix(time-saved): renames all variable associated with timing reports.
  [Frank Harrison]

  This just makes someting which can become intractable/confusing a lot
  easier to follow.
- Fix(time-saved): check that time-saved is reported correctly. [Frank
  Harrison]

  Here we add a test first and then fix the missing math to calculate the
  time-saved by using runem. We broke this in the previous feature for
  rendering the tree slightly more elegantly.
- Feat(hide-single-leafs): only show the job when it has a single child.
  [Frank Harrison]

  We would get duplicated information for jobs which had single
  run_command invocations. This only shows sub-tasks/jobs if there are
  more than one sub-tasks meaning the output looks a lot nicer & clearer.
- Chore(deps): adds setuptools as a explicit dep. [Frank Harrison]

  ... otherwise we get the following error (more often in python 3.12),
  perhaps due to setuptools being removed from distros?:

  ```text
  Traceback (most recent call last):
    File "/var/www/mydir/virtualenvs/dev/bin/pip", line 5, in <module>
      from pkg_resources import load_entry_point
  ImportError: No module named pkg_resources
  ```
- Merge pull request #39 from lursight/feat/time_all_run_command_calls.
  [Frank Harrison]

  Feat/time all run command calls
- Feat(pretty-tree): refactors out the phase-job report generator.
  [Frank Harrison]

  This is just to make pylint happy.
- Feat(pretty-tree): makes the report tree neater. [Frank Harrison]
- Feat(time-all-sub-tasks): re-raise errors for context in ci/cd. [Frank
  Harrison]

  In github ci/cd we were hitting the asserts but had no context of where
  they're raised from or why. This should fix that if they still occur.
- Feat(time-all-sub-tasks): adds a test to test the time-recording
  functions. [Frank Harrison]
- Feat(time-all-sub-tasks): adds all run_command times to report output.
  [Frank Harrison]
- Chore(type): uses a type-alias instead of manual type. [Frank
  Harrison]
- Merge pull request #37 from
  lursight/dependabot/github_actions/actions/upload-artifact-4. [Frank
  Harrison]

  chore(deps): bump actions/upload-artifact from 3 to 4
- Chore(deps): bump actions/upload-artifact from 3 to 4.
  [dependabot[bot]]

  Bumps [actions/upload-artifact](https://github.com/actions/upload-artifact) from 3 to 4.
  - [Release notes](https://github.com/actions/upload-artifact/releases)
  - [Commits](https://github.com/actions/upload-artifact/compare/v3...v4)

  ---
  updated-dependencies:
  - dependency-name: actions/upload-artifact
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- Merge pull request #36 from lursight/chore/more_python_versions_in_ci.
  [Frank Harrison]

  Chore/more python versions in ci
- Chore(github-ci): workaround for python 3.12 setuptools issue. [Frank
  Harrison]

  This fies what looks like an issue with pytest hooks running ci/cd (and
  on local machine) where we get:
    ModuleNotFoundError: No module named 'pkg_resources'
- Chore(github-ci): updates the python `--help` tests for 3.11 (and
  later) [Frank Harrison]
- Chore(github-ci): test python 3.9, 3.11 and 3.12 in ci. [Frank
  Harrison]

  We don't bother with 3.10 because we test 3.9 and boundaries for
  features are on the 3.11 version.

  We don't bother with earlier than 3.9, even though 3.8 is the earliest
  officially supported version.


0.0.28 (2024-03-01)
-------------------
- Release: version 0.0.28 🚀 [Frank Harrison]
- Merge pull request #35 from lursight/fix/aliases_not_setting_options.
  [Frank Harrison]

  Fix/aliases not setting options
- Switches the API so 'read-only' Options are the prominent type. [Frank
  Harrison]

  ... and Writable are the recessive type, making it easier for API users to ensure they're using the correct type
- Uses OptionsReadOnly, stopping accidentally overwritting options by
  individual jobs. [Frank Harrison]
- Adds a read-only version of the Options dict. [Frank Harrison]
- Ports Options type to an InformativeDict. [Frank Harrison]

  This shows you what options are available in the options dict if you
  look up a value that doesn't exist.
- Updates logging for clarity. [Frank Harrison]
- Merge pull request #34 from lursight/chore/github-actions. [Frank
  Harrison]

  Chore/GitHub actions
- Chore(github-ci): knocks out windows ci/cd for now. [Frank Harrison]
- Chore(github-ci): sets the windows ci to use utf-8. [Frank Harrison]
- Chore(github-ci): HACK ignore coverage in tested code. [Frank
  Harrison]

  It's not cler why the ci/cd thinks this isn't being hit, it is locally
  and I can't figure out why it wouldn't be on the ci/cd, perhaps it's
  down to the multithreaded pytest runs, but that would be
  non-deterministic. This will probably need looking into at some point.
- Chore(ci-coverage): updates the _get_jobs_matching test case. [Frank
  Harrison]

  Making it more explicit and easier to follow
- Chore(ci-coverage): fixes the help-test false-positive. [Frank
  Harrison]

  We were always writing the help"
- Chore(ci-coverage): adds test for
  test_run_command_basic_call_verbose_with_cwd. [Frank Harrison]
- Chore(ci-coverage): ignores un-hit 'communicate' mock function. [Frank
  Harrison]
- Chore(github-ci): upload reports on failures. [Frank Harrison]
- Chore(github-ci): revert back to using the makefile for the redundant
  checks. [Frank Harrison]
- Chore(github-ci): installs yarn deps for ci job. [Frank Harrison]
- Chore(github-ci): makes the log output less verbose by using --no-
  spinner. [Frank Harrison]
- Chore(github-ci): moves the redundancy checks first to own job. [Frank
  Harrison]
- Chore(github-ci): runs two basic checks for redunancy during ci.
  [Frank Harrison]

  This should help catch errors where runem has been broken and returns a
  false-positive when run against itself.
- Chore(github-ci): runs runem against itself. [Frank Harrison]

  This could have drawbacks later so we will think about adding some
  redundancy to the ci checks.
- Merge pull request #33 from lursight/fix/mutiline_stdout. [Frank
  Harrison]

  fix(stdout-parsing): ensures that trailing newlines are handled
- Fix(stdout-parsing): ensures that trailing newlines are handled.
  [Frank Harrison]

  There will be a slight performance cost to this, hopefully not too much.


0.0.27 (2024-02-26)
-------------------
- Release: version 0.0.27 🚀 [Frank Harrison]
- Merge pull request #32 from lursight/feat/min-version_check. [Frank
  Harrison]

  Feat/min version check
- Feat(min-version): adds support to check for minimum required runem
  version in config. [Frank Harrison]
- Feat(min-version): adds --version switch. [Frank Harrison]

  and changes -v to be an alias for --version and not --verbose


0.0.26 (2024-02-25)
-------------------
- Release: version 0.0.26 🚀 [Frank Harrison]
- Merge pull request #31 from
  lursight/fix/exceptions_on_non_blocking_print. [Frank Harrison]

  fix(blocked-print): adds a 'blocking_print' function
- Fix(blocked-print): adds a 'blocking_print' function. [Frank Harrison]

  Sometimes in long-lasting jobs, that produce lots of output, we hit
  BlockingIOError where we can't print to screen because the buffer is full or
  already being written to (for example), i.e. the  would need to be a
  'blocking' call, which it is not.


0.0.25 (2024-02-24)
-------------------
- Release: version 0.0.25 🚀 [Frank Harrison]
- Merge pull request #30 from lursight/feat/stream_stdout. [Frank
  Harrison]

  Feat/stream stdout
- Feat(stream-stdout): supports larger sub-process buffer sizes by using
  Popen. [Frank Harrison]

  This also allows us to stream the stdout to the console on verbose mode
- Chore(flake8): upgrades to latest flake8. [Frank Harrison]


0.0.24 (2024-02-13)
-------------------
- Release: version 0.0.24 🚀 [Frank Harrison]
- Feat(spinner-visibility-option): adds option to hide spinner. [Frank
  Harrison]
- Merge pull request #25 from
  lursight/dependabot/github_actions/codecov/codecov-action-4. [Frank
  Harrison]

  chore(deps): bump codecov/codecov-action from 3 to 4
- Chore(deps): bump codecov/codecov-action from 3 to 4.
  [dependabot[bot]]

  Bumps [codecov/codecov-action](https://github.com/codecov/codecov-action) from 3 to 4.
  - [Release notes](https://github.com/codecov/codecov-action/releases)
  - [Changelog](https://github.com/codecov/codecov-action/blob/main/CHANGELOG.md)
  - [Commits](https://github.com/codecov/codecov-action/compare/v3...v4)

  ---
  updated-dependencies:
  - dependency-name: codecov/codecov-action
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...


0.0.23 (2024-02-09)
-------------------
- Release: version 0.0.23 🚀 [Frank Harrison]
- Merge pull request #28 from lursight/feat/add_cwd_to_run_command.
  [Frank Harrison]

  feat(cwd): adds cwd to run_command
- Feat(cwd): adds cwd to run_command. [Frank Harrison]


0.0.22 (2024-02-08)
-------------------
- Release: version 0.0.22 🚀 [Frank Harrison]
- Merge pull request #27 from lursight/feat/add_cwd_to_run_command.
  [Frank Harrison]

  feat(cwd_in_run_command): allows cwd to be passed to run_command
- Feat(cwd_in_run_command): allows cwd to be passed to run_command.
  [Frank Harrison]

  This is despite the fact that runem already manually sets the cwd when running tasks
- Merge pull request #26 from
  lursight/chore/reudce_complexity_of_run_command. [Frank Harrison]

  chore(simplify-run_command): reduces the complexity of run_command
- Chore(simplify-run_command): reduces the complexity of run_command.
  [Frank Harrison]

  This is ahead of adding a cwd paramter to it


0.0.21 (2024-02-02)
-------------------
- Release: version 0.0.21 🚀 [Frank Harrison]
- Merge pull request #24 from lursight/feat/add_ctx_dir_as_tag. [Frank
  Harrison]

  feat(ctx-dir-tag): add the last directory name from the 'cwd' path as a tag
- Feat(ctx-dir-tag): add the last directory name from the 'cwd' path as
  a tag. [Frank Harrison]
- Merge pull request #23 from lursight/chore/update_docs. [Frank
  Harrison]

  chore(docs): improves docs slightly
- Chore(docs): improves docs slightly. [Frank Harrison]
- Merge pull request #22 from lursight/fix/help_text_test. [Frank
  Harrison]

  Fix/help text test
- Chore(cover-report-on-error): covers missed cases. [Frank Harrison]

  We weren't testing the exception handling-and-return cases of the code.
- Chore(fix-spinner-coverage): parameterises a test to cover no-show
  cases. [Frank Harrison]

  We didn't have coverage on the no-show-spinner cases. These parameters add
  that coverage.
- Chore(fix-tags-coverage): removed redundant code in get_tags. [Frank
  Harrison]

  This fixes coverage in get_tags by removing a case already covered.

  The case is one where we have already tested for the existence of valid
  tags and returned 'None', we were doing it twice.
- Fix(help-text-test): fixes the help output, again. [Frank Harrison]

  Adding more switches to runem cli changes the usage line significantly.
  This addresses that by only removing the problematic bit __main__ or -c
  and not the rest of the switches.

  We do this because the rest of the switches might be on the 'usage:'
  line or wrapped on the line below.

  The differences come from when running via xdist or single-threaded
  pytest and would presumably also manifest in other threaded environs
- Feat(one-line-commands): fixes typo in README. [Frank Harrison]
- Merge pull request #21 from lursight/feat/one_liners. [Frank Harrison]
- Feat(one-line-commands): Update README.md reflecting all new features.
  [Frank Harrison]

  ... also clarifies various aspects and improves the "sell" i.e. why
  runem is useful.
- Feat(one-line-commands): adds troubleshooting documentation. [Frank
  Harrison]
- Feat(one-line-commands): documents oneliners. [Frank Harrison]
- Feat(one-line-commands): simplifies the default tags. [Frank Harrison]

  ... mainly removing the unused 'UNTAGGED_TAG' flag as we favour 'None' now.
- Feat(one-line-commands): adds simple-command to the e2e tests. [Frank
  Harrison]

  This captures many more issues wit the new changes, enureing we 'know'
  what the output and behaviour is with these new types of jobs

  Also ensure tag tests work on ci/cd
- Feat(one-line-commands): adds simple-commands support to runem. [Frank
  Harrison]

  This is quite a big refactor to add one-liners to .runem.yml, improving
  the speed of on-boarding.

  This means that the quick route to use should be a .runem.yml file that
  looks something like:

  ```yml
  - job:
      command: echo "hello world!"
  ```

  instead of needing the following two files
  ```yml
  - job:
      addr:
        file: path/to/file.py
        function: _function_name
      label: Job Label
      when:
        phase: some_phase
        tags:
          - tag
  ```

  ```py
  from runem.run_command import run_command
  from typing import Any

  def _function_name(*kwargs:Any) -> None:
    run_command(["echo", "hello world"], **kwargs)
  ```

  So, that's 2 lines instead of 15 so 87% less code just to get started.

  Note that the key difference the 'address' and 'command' entries.

  Also note that almost all of the options are now optional. This means
  that the above function-addressed config can just be the following:

  ```yml
  - job:
      addr:
        file: path/to/file.py
        function: _function_name
      label: Job Label
  ```

  We use 'shlex' to avoid the word splitting problem when parsing commands
  to be run.

  There are some rough edges around tag handling, that we should tackle
  before releasing.
- Feat(one-line-commands): makes config-parsing unit-test explicit.
  [Frank Harrison]

  Adds specific exception checking for the case we are looking for ahead
  of changing the behaviour in this section.
- Feat(one-line-commands): moves the get_job_wrapper() manager to own
  file. [Frank Harrison]

  Clarifying that we have job-function variants move the selection
  function to its own file.
- Feat(one-line-commands): prepares get_job_wrapper() to support
  variants. [Frank Harrison]

  We are going to want to support multiple types of job-functions, so here
  we split out the get_job_wrapper() into the get_job_wrapper_py_func()
  variant ahead of adding a simple-command variant.
- Merge pull request #20 from lursight/chore/tidy. [Frank Harrison]

  chore(tidy): removes lursight specific env variables
- Chore(tidy): removes lursight specific env variables. [Frank Harrison]
- Merge pull request #19 from lursight/feat/improve_log_output. [Frank
  Harrison]

  Feat/improve log output
- Fix(align-bar-graphs): aligns floats with varying orders of magnitude.
  [Frank Harrison]

  Without this, when we have a task that take 1s and another that takes
  120, the bar graphs don't align and it's hard to see the comparison
- Fix(align-bar-graphs): changes tests to show the key issue with
  floats. [Frank Harrison]
- Feat(less-logging): reduce the amount of logging in verbose=False.
  [Frank Harrison]

  Most of the time you don't want lots of logging, you just want to
  run-and-done.
- Merge pull request #18 from
  lursight/feat/show_reports_even_on_failure. [Frank Harrison]

  Feat/show reports even on failure
- Fix(logging-consistency): adds a test against the output when a job-
  function raises. [Frank Harrison]
- Fix(logging-consistency): adds stdout tests to the job_execute()
  tests. [Frank Harrison]

  This allows me to add a test to ensure the error output isn't shown
  twice in failed-command cases
- Feat(report-before-error): shows the available reports on error,
  before re-raising the error. [Frank Harrison]
- Fix(logging-consistency): puts first stdout line with prefix. [Frank
  Harrison]


0.0.20 (2024-01-12)
-------------------
- Release: version 0.0.20 🚀 [Frank Harrison]
- Merge pull request #17 from lursight/feat/multiple_cwd. [Frank
  Harrison]

  Feat/multiple cwd
- Feat(multi-cwd): clones jobs for each cwd path given in .runem.yml.
  [Frank Harrison]

  Allows a job to have multiple cwds. That job will then be run once for
  each of those cwds.

  This make running individual commands across many project path much
  easier and faster as the normal is to run them in serial.

  This gives us reporting on each path bit as well as faster completion of
  tasks.
- Feat(multi-cwd): adds annotation to bit where we add jobs. [Frank
  Harrison]
- Chore(typo): fixes a typo in a variable. [Frank Harrison]
- Chore(docs): removes defunct comment. [Frank Harrison]
- Fix(stdout): ensure the job filter log output is tidier and sorted.
  [Frank Harrison]


0.0.19 (2024-01-10)
-------------------
- Release: version 0.0.19 🚀 [Frank Harrison]
- Merge pull request #16 from lursight/feat/in-progress-job-count.
  [Frank Harrison]

  Feat/in progress job count
- Feat(in-progress-job-count): shows num jobs completed in halo ticker.
  [Frank Harrison]

  This gives better feedback about what runem is doing to the user and
  reduces frustration for long-running tasks.
- Chore(coverage): adds more explicit coverage to code that will need it
  later. [Frank Harrison]
- Merge pull request #14 from lursight/chore/add_vscode_runner. [Frank
  Harrison]

  Chore/add vscode runner
- Chore(vs-code): configures vscode's test runner. [Frank Harrison]
- Chore(vs-code): adds a launch.json for debugging in vscode. [Frank
  Harrison]
- Merge pull request #13 from lursight/chore/tidy_pull_request_template.
  [Frank Harrison]

  chore: updates the PR template
- Chore: updates the PR template. [Frank Harrison]

  ... making it less annoying to use
- Merge pull request #12 from lursight/chore/remove_rename_try_2. [Frank
  Harrison]

  chore: removes the rename-project action from workflows
- Chore: removes the rename-project action from workflows. [Frank
  Harrison]
- Merge pull request #11 from lursight/chore/fix_mypy_checks. [Frank
  Harrison]

  chore(fix-mypy-config): ensures mypy catches all error (strict mode)
- Chore(mypy): upgrade mypy 1.7.0 -> 1.8.0. [Frank Harrison]
- Chore(fix-mypy): fixes spurious test-types. [Frank Harrison]

  This is a heavier "fix" than just a chore, but not really a fix either.

  Basically the test was writing an invalid yml file and the code supported
  that bad behaviour. This replaces that buggy test with a correctly typed
  one and adds some earlier conformance to the config loader for a
  (hopefully) minor functional change.
- Chore(fix-mypy): fixes the various type issues. [Frank Harrison]
- Chore(fix-mypy-config): adds noddy detector for if mypy.ini is
  invalid, as reported by mypy. [Frank Harrison]
- Chore(fix-mypy-config): fixes comments being included as option
  values. [Frank Harrison]

  We had comments after each option in mypy.ini which the mypy ini parser
  couldn't process. We put the comments first now.
- Merge pull request #10 from lursight/feat/show_num_worker. [Frank
  Harrison]

  feat(show-num-workers): show max workers in output
- Feat(show-num-workers): show max workers in output. [Frank Harrison]


0.0.18 (2024-01-09)
-------------------
- Release: version 0.0.18 🚀 [Frank Harrison]
- Merge pull request #9 from lursight/chore/rename_core_functions.
  [Frank Harrison]

  Chore/rename core functions
- Chore(core-func-rename): renames functions and fixes imports. [Frank
  Harrison]
- Chore(core-func-rename): renames files to better reflect contents.
  [Frank Harrison]
- Merge pull request #8 from lursight/chore/more_typing_strictness.
  [Frank Harrison]

  Chore/more typing strictness
- Chore(mypy-strict): switches mypy to use strict-mode. [Frank Harrison]

  This should catch more issues down the line
- Chore(mypy-strict): enable disallow_untyped_calls and annotate it.
  [Frank Harrison]
- Chore(mypy-strict): enable disallow_untyped_defs in mypy. [Frank
  Harrison]
- Chore(mypy-strict): enables check_untyped_defs in mypy. [Frank
  Harrison]
- Chore(mypy-strict): annotates mypy config options. [Frank Harrison]
- Merge pull request #7 from lursight/chore/project_status. [Frank
  Harrison]

  chore(project-status): removes the project rename from actions
- Chore(project-status): removes the project rename from actions. [Frank
  Harrison]
- Merge pull request #5 from lursight/feat/job_spinner. [Frank Harrison]

  Feat/job spinner
- Feat(progress): gets a progress spinner working. [Frank Harrison]
- Feat(progress): adds way to track running jobs for multip-proc jobs.
  [Frank Harrison]
- Merge pull request #3 from
  lursight/dependabot/github_actions/actions/setup-python-5. [Frank
  Harrison]

  chore(deps): bump actions/setup-python from 4 to 5
- Chore(deps): bump actions/setup-python from 4 to 5. [dependabot[bot]]

  Bumps [actions/setup-python](https://github.com/actions/setup-python) from 4 to 5.
  - [Release notes](https://github.com/actions/setup-python/releases)
  - [Commits](https://github.com/actions/setup-python/compare/v4...v5)

  ---
  updated-dependencies:
  - dependency-name: actions/setup-python
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- Merge pull request #6 from lursight/fix/help_tests. [Frank Harrison]

  Fix/help tests
- Chore(fix-help-tests): fixing the help-text test in ci/cd. [Frank
  Harrison]
- Chore(pytest): stops reporting of coverage on test failures. [Frank
  Harrison]
- Chore(pytest): stops failing coverage BEFORE we want to. [Frank
  Harrison]
- Chore(type): fixes type errors. [Frank Harrison]
- Merge pull request #4 from lursight/fix/python3.10_support. [Frank
  Harrison]

  fix(python3.10): removes another pipe shortcut
- Fix(python3.10): removes another pipe shortcut. [Frank Harrison]
- Merge branch 'fix/python3.10_support' [Frank Harrison]
- Fix(python3.10): removes newer typing syntax. [Frank Harrison]
- Merge branch 'fix/coverage' [Frank Harrison]
- Fix(coverage): adds more coverage to parse_config() [Frank Harrison]

  ... specifically the bit that warns if we have to nordered phases
- Fix(coverage): adds more coverage to
  _load_python_function_from_module() [Frank Harrison]
- Fix(coverage): adds more coverage to initialise_options() [Frank
  Harrison]
- Fix(coverage): adds more coverage to report.py. [Frank Harrison]
- Fix(coverage): annotates a file that needs more coverage. [Frank
  Harrison]
- Merge branch 'fix/spell_check' [Frank Harrison]
- Fix(spell-check): fixes the spell-checker by ignoring the history
  file. [Frank Harrison]

  ... which contains typos in the commit hitsory


0.0.17 (2023-12-09)
-------------------
- Release: version 0.0.17 🚀 [Frank Harrison]
- Merge branch 'chore/run_in_check_mode_on_release' [Frank Harrison]
- Chore(release-checks): makes each command fail on 'make release'
  [Frank Harrison]
- Chore(release-checks): run runem in check mode on 'make release'
  [Frank Harrison]
- Merge branch 'fix/pyyaml_dep' [Frank Harrison]
- Fix(deps): adds the py-yaml dep to release requirements. [Frank
  Harrison]
- Merge branch 'chore/log_output' [Frank Harrison]
- Chore(coverage): fixes up coverage, for now. [Frank Harrison]
- Fixup: logs. [Frank Harrison]
- Chore(black): formats log.py. [Frank Harrison]
- Chore(log-format): replaces print() with log. [Frank Harrison]

  ... also adds a prefix to the logging
- Merge branch 'chore/skip_spell_check_history' [Frank Harrison]
- Chore(spell-history): add cSpell:disable to HISTORY.md's frontmatter.
  [Frank Harrison]

  ... because some of the commit messages contain spelling typos


0.0.16 (2023-12-05)
-------------------
- Release: version 0.0.16 🚀 [Frank Harrison]
- Merge branch 'chore/get_release_running_tests' [Frank Harrison]
- Chore(test-on-release): prints existing tags on make release. [Frank
  Harrison]
- Chore(test-on-release): run tests after choosing tag. [Frank Harrison]
- Merge branch 'chore/test' [Frank Harrison]
- Chore(test-and-cov): fails tests if not 100% [Frank Harrison]
- Chore(test-and-cov): gets reports to 100% coverage. [Frank Harrison]
- Chore(test-and-cov): gets job_runner to 100% coverage. [Frank
  Harrison]

  ... TODO: actually test returns and side-effects of calls
- Chore(test-and-cov): adds test for runner to read job-context. [Frank
  Harrison]
- Chore(test-and-cov): adds test for run_command with empty files.
  [Frank Harrison]

  ... should cause an early return
- Chore(test-and-cov): adds basic tests for the job-runner. [Frank
  Harrison]
- Chore(test-and-cov): test missing options. [Frank Harrison]
- Chore(test-and-cov): mocks the actuall threaded runner, not saving any
  real time, but it is something I will consider again and again. [Frank
  Harrison]
- Chore(test-and-cov): adds test to test filter in/out jobs --phases,
  --jobs, --tags. [Frank Harrison]
- Chore(test-and-cov): moves help-text into separate file for easier
  updating. [Frank Harrison]
- Chore(test-and-cov): adds end-to-end test for bad --jobs, --tags,
  --phases switches. [Frank Harrison]
- Chore(test-and-cov): puts --help under test. [Frank Harrison]

  ... fixing non deterministic output
- Chore(test-and-cov): puts the end-2-end upder more test. [Frank
  Harrison]
- Chore(test-and-cov): documents and splits out those but where we do
  the heavy lifting in terms of job-running. [Frank Harrison]
- Chore(test-and-cov): moves ConfigMetadata to own file. [Frank
  Harrison]
- Chore(test-and-cov): unifies many disperate control vars under
  ConfigMetadata. [Frank Harrison]

  This reduces the amount of code, simplifies concepts and overall makes
  it easier to reason about what is going on.
- Chore(test-and-cov): splits out the remaining uncovered code from
  runem.py. [Frank Harrison]
- Chore(test-and-cov): attempts to add a full config end-to-end test.
  [Frank Harrison]
- Chore(test-and-cov): gets config_parse to 100% coverage. [Frank
  Harrison]
- Chore(test-and-cov): puts find_files() under test. [Frank Harrison]
- Chore(test-and-cov): adds more test-coverage and splits up code to
  support it. [Frank Harrison]
- Chore(test-and-cov): adds test for end-to-end running of runem. [Frank
  Harrison]
- Chore(test-and-cov): splits load_config out so it can be mocked.
  [Frank Harrison]
- Chore(test-and-cov): removes the setup.py from code-coverage. [Frank
  Harrison]
- Chore(test-and-cov): tests that run_command handles runs failing to
  start the process and other errors. [Frank Harrison]
- Chore(test-and-cov): adds test to run_command covering 'ignore_fails'
  [Frank Harrison]
- Chore(test-and-cov): adds test to run_command covering env-overrides.
  [Frank Harrison]
- Chore(test-and-cov): puts run_command under-test. [Frank Harrison]

  ... mainly the normal success and failure routes in verbose and non
  verbose modes, along side the allowed_exit codes
- Chore(test-and-cov): tests and annotates 'get_std_out' [Frank
  Harrison]
- Chore(test-and-cov): puts cli.py under test. [Frank Harrison]
- Chore(test-and-cov): adds basic test for _parse_job_config. [Frank
  Harrison]

  ... not a great test, but it's a start
- Feat(better-config-error): preints the missing key on job loading.
  [Frank Harrison]
- Feat(reports): adds methods for return reports to be reported at the
  end of runs. [Frank Harrison]
- Chore(pytest): configures coverage properly. [Frank Harrison]
- Chore(pytest): adds a pytest job. [Frank Harrison]

  Gets the test passing also
- Chore(pytest): fixes the typing of the go_to_tmp_path fixture. [Frank
  Harrison]
- Chore(test-hooks-package): fixes the .runem config references to
  test_hooks. [Frank Harrison]
- Chore(test-hooks-package): adds a py.typed to the test-hooks package
  fixing a mypy issue. [Frank Harrison]
- Chore(test-hooks-package): makes test_hooks a package instead of the
  parent scripts/ [Frank Harrison]
- Chore(test-hooks-package): renames test-hooks -> test_hooks making it
  a valid python package. [Frank Harrison]
- Chore(lint): fixes line-to-long issue. [Frank Harrison]
- Merge branch 'chore/spell' [Frank Harrison]
- Chore(spell): fixes spelling. [Frank Harrison]
- Chore(spell): deletes call-graph code that was lursight-specific.
  [Frank Harrison]


0.0.15 (2023-12-02)
-------------------
- Release: version 0.0.15 🚀 [Frank Harrison]
- Merge branch 'feat/add_optional_ctx_config' [Frank Harrison]
- Chore(json-check): adds validation for if a file exists in json-
  validate. [Frank Harrison]
- Chore: black. [Frank Harrison]
- Chore(test-profile): flags that the profile option isn't actually used
  yet. [Frank Harrison]
- Feat(defaults): allows the 'ctx' config to default to root_dir and the
  other config to not exist. [Frank Harrison]

  ... as limitFilesToGroup isn't actually used


0.0.14 (2023-11-29)
-------------------
- Release: version 0.0.14 🚀 [Frank Harrison]
- Merge branch 'fix/working_from_non-root_dirs' [Frank Harrison]
- Chore(logs): reduces duplicate log out for tag-filters. [Frank
  Harrison]
- Fixup: fixes the labels used for some jobs after simplifying params.
  [Frank Harrison]
- Fix(git-ls-files): chdir to the cfg dir so git-ls-files picks up all
  file. [Frank Harrison]

  .... of course this assumes that the file is next to the .git directory
- Fix(job.addr): anchors the function-module lookup to the cfg file.
  [Frank Harrison]

  This should now be much more consistent.
- Fix(job.addr): removes deprecated code for hooks in main runem file.
  [Frank Harrison]


0.0.13 (2023-11-29)
-------------------
- Release: version 0.0.13 🚀 [Frank Harrison]
- Merge branch 'feat/better_module_find_error_msg' [Frank Harrison]
- Feat(better-module-msg): improves the information given when loading a
  job address. [Frank Harrison]


0.0.12 (2023-11-29)
-------------------
- Release: version 0.0.12 🚀 [Frank Harrison]
- Merge branch 'chore/format_yml' [Frank Harrison]
- Chore(format-yml): reformats the .runem.yml file. [Frank Harrison]
- Chore(format-yml): adds yml files to the prettier command. [Frank
  Harrison]

  This means that runems own runem config is reformatted
- Merge branch 'feat/warn_on_bad_names' [Frank Harrison]
- Feat(bad-label): errors on bad labels. [Frank Harrison]

  .. not a massive improvment but really helps clarify what you SHOULD be looking at when things go wrong, which is nice
- Feat(bad-func-ref-message): gives a better error message on bad
  function references. [Frank Harrison]

  Specifically when those functions cannot be found inside the file/module
  that they're reference to by the .runem.yml
- Merge branch 'chore/pretty_json' [Frank Harrison]
- Chore(pretty-json): prettifies cspell.json. [Frank Harrison]
- Chore(pretty-json): adds jobs to use prettifier via yarn. [Frank
  Harrison]

  ... currently this only targets json files
- Merge branch 'chore/kwargs' [Frank Harrison]
- Chore(kwargs): makes run_command 'cmd' the first thing as it cannot be
  infered from the runem kwargs. [Frank Harrison]
- Feat(kwargs): moves to using kwargs by preference when calling jobs.
  [Frank Harrison]

  ... jobs can then pass those kwargs down to the run_command
- Chore(kwargs): deletes 0xDEADCODE. [Frank Harrison]

  This deletes deadcode that was left over from the move out of the lursight codebase


0.0.11 (2023-11-29)
-------------------
- Release: version 0.0.11 🚀 [Frank Harrison]
- Merge branch 'fix/warning_when_no_files_for_job' [Frank Harrison]
- Fix(warn-no-files): starts troubleshooting. [Frank Harrison]
- Fix(warn-no-files): updates README after deleting defunct jobs. [Frank
  Harrison]
- Fix(warn-no-files): removes defunct job-specs. [Frank Harrison]
- Fix(warn-no-files): ads more information when a job isn't run because
  of files. [Frank Harrison]

  TBH this shows a problem in the spec method


0.0.10 (2023-11-29)
-------------------
- Release: version 0.0.10 🚀 [Frank Harrison]
- Merge branch 'docs/update_readme' [Frank Harrison]
- Docs: make readme more readable. [Frank Harrison]


0.0.9 (2023-11-29)
------------------
- Release: version 0.0.9 🚀 [Frank Harrison]
- Merge branch 'fix/remove_lursight_env_refs' [Frank Harrison]
- Fix(lursight-envs): removes lursight envs from runem. [Frank Harrison]


0.0.8 (2023-11-28)
------------------
- Release: version 0.0.8 🚀 [Frank Harrison]
- Merge branch 'chore/add_spell_check' [Frank Harrison]
- Chore(spell-check): disallows adolescent word. [Frank Harrison]
- Chore(spell-check): adds spell-check job for runem. [Frank Harrison]
- Merge branch 'chore/minor_improvement_of_log_output_and_report' [Frank
  Harrison]
- Chore(report): puts the runem times first in the report and indents.
  [Frank Harrison]

  ... also replaces 'run_test' with 'runem'
- Chore(logs): reduce log verbosity in non-verbose mode. [Frank
  Harrison]

  ... but make it MORE useful in verbose mode.
- Chore(logs): further reduce spurious output. [Frank Harrison]


0.0.7 (2023-11-28)
------------------
- Release: version 0.0.7 🚀 [Frank Harrison]
- Merge branch 'chore/typos' [Frank Harrison]
- Chore(typos): fixes a typos when warning about 0-jobs. [Frank
  Harrison]
- Chore(typos): stops the cmd_string printing twice. [Frank Harrison]

  on error with ENVs the command string was printed twice


0.0.6 (2023-11-28)
------------------
- Release: version 0.0.6 🚀 [Frank Harrison]
- Merge branch 'chore/branding' [Frank Harrison]
- Chore(logs): reduces the log out put for jobs that aren't being run.
  [Frank Harrison]
- Docs: updates the TODOs. [Frank Harrison]
- Docs: change references to lursight to runem. [Frank Harrison]


0.0.5 (2023-11-28)
------------------
- Release: version 0.0.5 🚀 [Frank Harrison]
- Merge branch 'feat/time_saved' [Frank Harrison]
- Docs: fixes the ambiguos language on the number of jobs/core being
  used. [Frank Harrison]
- Feat(time-saved): shows the time saved vs linear runs on DONE. [Frank
  Harrison]
- Chore(progressive-terminal): unifies two subprocess.run calls by
  allowing the env to be None. [Frank Harrison]
- Docs: adds --tags and --phases to the docs. [Frank Harrison]


0.0.4 (2023-11-27)
------------------
- Release: version 0.0.4 🚀 [Frank Harrison]
- Chore(typing): moves py.typed into package src dir. [Frank Harrison]


0.0.3 (2023-11-27)
------------------
- Release: version 0.0.3 🚀 [Frank Harrison]
- Chore(typing): adds the py.typed to the manifest. [Frank Harrison]


0.0.2 (2023-11-27)
------------------
- Release: version 0.0.2 🚀 [Frank Harrison]
- Chore(typing): adds a py.typed marker file for upstream mypy tests.
  [Frank Harrison]


0.0.1 (2023-11-27)
------------------
- Release: version 0.0.1 🚀 [Frank Harrison]
- Chore(release): moves release to script. [Frank Harrison]

  It wasn't working because read -p wasn't setting the TAG variabl for
  some reason, I suspect because of the makefile.
- Merge branch 'chore/update_ci_cd_black' [Frank Harrison]
- Chore(black-ci-cd): removes line-limit sizes for pyblack runs in
  actions. [Frank Harrison]
- Merge branch 'chore/fix_sponsorship_link' [Frank Harrison]
- Chore(sponsorship): fixes a link to sponsorship. [Frank Harrison]
- Merge branch 'chore/rename_job_spec_file' [Frank Harrison]
- Chore(config-rename): renames the config file to match the name of the
  project. [Frank Harrison]
- Merge branch 'docs/updating_docs_ahead_of_release' [Frank Harrison]
- Docs: builds the docs using the base README. [Frank Harrison]
- Fix(deps): merges the deps after merging the code into the template.
  [Frank Harrison]
- Chore(docs): updates the landing README.md. [Frank Harrison]
- Merge branch 'feat/run-time_reporting' [Frank Harrison]
- Feat(report): adds report graphs to end of run. [Frank Harrison]
- Merge branch 'fix/phase_order_running' [Frank Harrison]
- Fix(phases): fixes the phase run-order. [Frank Harrison]
- Merge branch 'chore/fixup_after_merge' [Frank Harrison]
- Chore(cli): gets the standalone 'runem' command connected up. [Frank
  Harrison]
- Chore(runem): further renames of run-test -> runem. [Frank Harrison]
- Chore(runem): moves all code run_test->runem. [Frank Harrison]
- Chore(runem): change run_test -> runem. [Frank Harrison]
- Chore(pre-release): revert version number to 0.0.0 until release.
  [Frank Harrison]
- Chore(mypy): adds type information for setuptools. [Frank Harrison]
- Chore(mypy): adds mypy config. [Frank Harrison]
- Chore(root-path): uses the config's path more often for looking up
  jobs. [Frank Harrison]
- Chore(root-path): uses the config path to anchor the root-path. [Frank
  Harrison]

  This fixes up how we detect the path to the functions
- Chore(format): black/docformatter. [Frank Harrison]
- Chore(ignore): adds vim-files to gitignore. [Frank Harrison]
- Chore(lint): removes defunct LiteralStrings (unused and unsupported)
  [Frank Harrison]
- Merge branch 'chore/prepare_files' [Frank Harrison]
- Chore(moves): fixes path-refs after move. [Frank Harrison]
- Chore(moves): moves files from old location. [Frank Harrison]
- Merge branch 'chore/pure_files_from_lursight_app' [Frank Harrison]
- Initial commit. [Frank Harrison]
- Merge pull request #1 from
  lursight/dependabot/github_actions/stefanzweifel/git-auto-commit-
  action-5. [Frank Harrison]

  Bump stefanzweifel/git-auto-commit-action from 4 to 5
- Bump stefanzweifel/git-auto-commit-action from 4 to 5.
  [dependabot[bot]]

  Bumps [stefanzweifel/git-auto-commit-action](https://github.com/stefanzweifel/git-auto-commit-action) from 4 to 5.
  - [Release notes](https://github.com/stefanzweifel/git-auto-commit-action/releases)
  - [Changelog](https://github.com/stefanzweifel/git-auto-commit-action/blob/master/CHANGELOG.md)
  - [Commits](https://github.com/stefanzweifel/git-auto-commit-action/compare/v4...v5)

  ---
  updated-dependencies:
  - dependency-name: stefanzweifel/git-auto-commit-action
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- Merge pull request #2 from
  lursight/dependabot/github_actions/actions/checkout-4. [Frank
  Harrison]

  Bump actions/checkout from 3 to 4
- ✅ Ready to clone and code. [dependabot[bot]]
- Bump actions/checkout from 3 to 4. [dependabot[bot]]

  Bumps [actions/checkout](https://github.com/actions/checkout) from 3 to 4.
  - [Release notes](https://github.com/actions/checkout/releases)
  - [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md)
  - [Commits](https://github.com/actions/checkout/compare/v3...v4)

  ---
  updated-dependencies:
  - dependency-name: actions/checkout
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- ✅ Ready to clone and code. [doublethefish]
- Initial commit. [Frank Harrison]


