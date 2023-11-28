Changelog
=========


(unreleased)
------------
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


