#!/usr/bin/env bash
#
# Push the current branch to origin and optionally create a PR (and enable
# auto-merge). Requires GitHub CLI (gh) for PR creation and auto-merge.
#
# Usage:
#   ./scripts/push_and_pr.sh [--auto-merge] [--title "PR title"] [--body "PR body"]
#
# Options:
#   --auto-merge   After creating the PR, run `gh pr merge --auto` so the PR
#                  merges when required checks pass. Requires maintainer (or
#                  admin) role and the repo to have auto-merge enabled in
#                  Settings → General → Pull Requests. If you lack permission,
#                  gh will exit with an error.
#   --title "..."  Title for the PR (default: current branch name).
#   --body "..."   Body for the PR (default: empty).
#
# Examples:
#   ./scripts/push_and_pr.sh
#   ./scripts/push_and_pr.sh --auto-merge
#   ./scripts/push_and_pr.sh --title "chore: add CI gate" --body "Adds ci_tests_gate."
#
set -o pipefail
set -e

AUTO_MERGE=false
PR_TITLE=""
PR_BODY=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --auto-merge)
      AUTO_MERGE=true
      shift
      ;;
    --title)
      PR_TITLE="$2"
      shift 2
      ;;
    --body)
      PR_BODY="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: $0 [--auto-merge] [--title \"...\"] [--body \"...\"]" >&2
      exit 1
      ;;
  esac
done

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ -z "$BRANCH" ]] || [[ "$BRANCH" == "HEAD" ]]; then
  echo "Could not determine current branch (detached HEAD?)." >&2
  exit 1
fi

echo "Pushing branch: $BRANCH"
if ! git push -u origin "$BRANCH"; then
  echo "Push failed." >&2
  exit 1
fi

if ! command -v gh &>/dev/null; then
  echo "GitHub CLI (gh) not found. PR not created. Open a PR manually on GitHub."
  exit 0
fi

# Create PR; use branch name as title if not provided
CREATE_ARGS=(pr create --head "$BRANCH")
[[ -n "$PR_TITLE" ]] && CREATE_ARGS+=(--title "$PR_TITLE") || CREATE_ARGS+=(--title "$BRANCH")
[[ -n "$PR_BODY" ]] && CREATE_ARGS+=(--body "$PR_BODY")

if ! gh "${CREATE_ARGS[@]}"; then
  echo "PR creation failed (e.g. PR may already exist for this branch)." >&2
  exit 1
fi

if [[ "$AUTO_MERGE" != "true" ]]; then
  exit 0
fi

echo "Enabling auto-merge (requires maintainer role and repo auto-merge enabled)."
if ! gh pr merge --auto --squash; then
  echo "Auto-merge failed. You may lack permission (maintainer/admin) or the repo may not have auto-merge enabled." >&2
  exit 1
fi

echo "Auto-merge enabled. PR will merge when required checks pass."
