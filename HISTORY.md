Changelog
=========


(unreleased)
------------
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


