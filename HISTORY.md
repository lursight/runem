Changelog
=========


(unreleased)
------------
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


