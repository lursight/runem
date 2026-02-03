#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2021 Frank Harrison <frank@doublethefish.com>, all rights reserved
# SPDX-License-Identifier: BSD-3-Clause
#
# Strict, defensive Bash mode
# - Fail fast on errors
# - Error on unset variables
# - Propagate failures through pipelines
# - Make ERR traps reliable
#

set -Eeuo pipefail
IFS=$'\n\t'   # Safer word-splitting (prevents bugs with spaces)

# ---- Error handling ---------------------------------------------------------

trap 'on_error $? $LINENO "$BASH_COMMAND"' ERR

on_error() {
  local exit_code="$1"
  local line_no="$2"
  shift 2
  local cmd=("$@")   # store ALL remaining args as an array

  printf >&2 'ERROR: exit=%s line=%s cmd=%q\nPWD: '%s'\n' \
    "$exit_code" "$line_no" "${cmd[*]}" "$(pwd)"
}

# ---- Safety ----------------------------------------------------------------

set -o noclobber   # Prevent accidental file overwrite via redirection (>)

# ---- Optional debugging ----------------------------------------------------
# Uncomment when diagnosing failures
# set -x            # Trace execution (VERY noisy)


# ---- Main script -----------------------------------------------------------

ORIGINAL_CHECKOUT="$(pwd)"
LOG_PREFIX="runem: pre-push: prep"
LOG_PBLANK="runem:               "

function RUN_LABELED_CMD() {
  # Run a command and prefix all output lines with a label.
  # Returns the exit code of the *command* (not sed).
  local label="$1"
  shift

  # Execute the command as argv (safe: preserves quoting/spacing).
  "$@" 2>&1 | sed -e "s/^/runem-push: ${label}: /g"

  # PIPESTATUS[0] is the exit code of "$@" (left side of the pipe).
  local exit_code="${PIPESTATUS[0]}"
  return "$exit_code"
}

# Get the root-checkout path of runem:
RUNEM_CHECKOUT=$(runem --root-show --silent | grep -v "runem: ")
if [ -z "$RUNEM_CHECKOUT" ]; then
  printf "RUNEM_CHECKOUT not set %s\\n" "$RUNEM_CHECKOUT"
  exit 2
fi

if [ ! -d "$RUNEM_CHECKOUT" ]; then
  printf "RUNEM_CHECKOUT path does not exist as dir %s\\n" "$RUNEM_CHECKOUT"
  exit 2
fi

if [ -z "$1" ]; then
  printf "%s please pass in test-isolation dir\\n" "$LOG_PREFIX"
  exit 22
fi
PRE_PUSH_TEST_DIR="$1"

# first clone the .git directory
printf "%s: cloning from: %s\\n" "$LOG_PREFIX" "$ORIGINAL_CHECKOUT"
printf "%s            to: %s\\n" "$LOG_PBLANK" "$PRE_PUSH_TEST_DIR"
printf "%s: max clone-size is: %s\\n" "$LOG_PREFIX" "$(du -sh $RUNEM_CHECKOUT/.git)" 
printf "%s                   : %s\\n" "$LOG_PBLANK" "$(du -sh $RUNEM_CHECKOUT/.pyenv)"


mkdir -p "$PRE_PUSH_TEST_DIR"

cd "$PRE_PUSH_TEST_DIR"
if [ ! -d ".git" ]; then
  # checkout is fresh
  RUN_LABELED_CMD "initialise git" git init
  RUN_LABELED_CMD "add remote" git remote add origin "$ORIGINAL_CHECKOUT"
fi

# Clean files that are untracked but NOT in .gitignore
# NOTE: This partially supports NO_CLEAN=1 by ensuring a minimal clean up is
#       performed before rsync.
RUN_LABELED_CMD "tmp-dir cleanup" git clean -fd

# Do a shallow, miinimal fetch
RUN_LABELED_CMD "shallow fetch" git fetch --all --depth=1

if [[ -n "${VIRTUALENV:-}" ]]; then
  RUN_LABELED_CMD "venv: VIRTUALENV" echo 
  RUN_LABELED_CMD "venv: deactivate prev" deactivate
fi

# Enter the test v-env
if [[ ! -d ".pyenv" ]]; then
  # Create the v-env
  RUN_LABELED_CMD "venv: init" uv venv --python 3.11 .pyenv
fi

RUN_LABELED_CMD "venv: enter pre-push venv" source .pyenv/bin/activate
