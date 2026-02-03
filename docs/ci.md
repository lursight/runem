# CI and branch protection

The project uses a single GitHub Actions workflow **CI** (`.github/workflows/main.yml`) that runs a matrix of tests (Python versions × OS). For branch protection and auto-merge, we expose **one** required check so you do not have to list each matrix combination.

## Required check: CI / ci_tests_gate

Configure branch protection to require only **CI / ci_tests_gate**. That single check runs after all matrix jobs and passes only when every matrix variant has succeeded. Adding or removing Python versions or runners does not change the required check name.

- **Settings → Branches → Branch protection** (for `main`): under "Require status checks before merging", add **CI / ci_tests_gate**.
- Do **not** require the individual matrix checks (e.g. "CI / ci_tests (3.9, ubuntu-latest)").

## Gate job behaviour

The gate job (`ci_tests_gate`) uses `if: always()` so it always runs and reports a status (it is never skipped). GitHub treats a *skipped* job as success for required checks, so without `if: always()`, a failing matrix could still allow merge.

| Result    | Meaning                    | Gate behaviour | When it happens |
| --------- | -------------------------- | -------------- | ---------------- |
| success   | All matrix jobs passed     | Pass           | Normal run.      |
| failure   | At least one matrix failed | Fail           | Test/build failure. |
| cancelled | Run/job cancelled          | Fail           | User or timeout cancel. |
| skipped   | Matrix job did not run     | Configurable   | Path filters, job `if`, or workflow not running that job. |

### When "skipped" is treated as pass (allow merge)

- **Path filters**: CI runs only when certain paths change (e.g. `src/`, `tests/`). Docs-only or config-only PRs skip the matrix; allowing "skipped" lets those PRs merge.
- **Job-level `if`**: The matrix job has a condition; when it is false the job is skipped. If that is intentional policy, the gate can pass.
- **Explicit skip**: Commit trailers or manual dispatch to skip CI; treating "skipped" as pass keeps behaviour consistent.

### When "skipped" is treated as fail (block merge)

- **Strict "always run" policy**: The matrix should run on every PR. If it is skipped (misconfiguration or GitHub behaviour), failing the gate blocks merge until someone re-runs or fixes.
- **Current default**: The workflow is configured so the gate **fails** when the matrix result is `skipped`. When you add path filters or explicit skip logic, update the gate step to treat `skipped` as pass in the same change and document it here.
