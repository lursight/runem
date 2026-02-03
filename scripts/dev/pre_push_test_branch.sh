# SPDX-FileCopyrightText: © 2021 Frank Harrison <frank@doublethefish.com>, all rights reserved
# SPDX-License-Identifier: BSD-3-Clause

# exit when any command fails
set -e

LOG_PREFIX="runem: pre-push: branch"

SHA_UNDER_TEST="$1"
BRANCH_UNDER_TEST="$2"
WORKING_DIR=$(realpath "$3")
printf "%s: branch-ref is '%s' (%s)\\n" "$LOG_PREFIX" "$BRANCH_UNDER_TEST" "$SHA_UNDER_TEST"
cd "$WORKING_DIR" || exit 77
printf "%s: working in %s\\n" "$LOG_PREFIX" "$PWD"

printf "%s: branches are\\n" "$LOG_PREFIX"
# we pipe to cat so we don't get blocking input prompts
git branch --all | cat

# checkout the branch under test
printf "%s: checking out branch-sha '%s' (%s)\\n" "$LOG_PREFIX" "$BRANCH_UNDER_TEST" "$SHA_UNDER_TEST"
# if we don't clean ahead of the chackout old files sometimes blocks checkout
#if [ -z "$NO_CLEAN" ]; then
#  git clean -xfd
#fi
git checkout -f "$SHA_UNDER_TEST" || exit 99

# clean any artefacts up and resetting the state to a pure state.
# printf "%s: resetting to head with hard, and cleaning'\\n" "$LOG_PREFIX"
#if [ -z "$NO_CLEAN" ]; then
#  git reset --hard head
#  git clean -xfd
#fi

printf "%s: setting up virtual environment\\n" "$LOG_PREFIX"

# activate the v-env
cd $WORKING_DIR/|| exit 10
activate () {
  . ./.pyenv/bin/activate
  # source ./.pyenv/bin/activate
}
activate # activate the env

# fail if we're not in the virtual-env
printf "%s: ensuring in virtual environment\\n" "$LOG_PREFIX"
python3 -c "import sys; sys.exit(99) if (sys.prefix == sys.base_prefix) else 0" || exit 99

printf "%s: installing/ensuring deps\\n" "$LOG_PREFIX"
python3 -m pip install ".[tests]"

printf "%s: running with python: %s: %s\\n" "$LOG_PREFIX" "$(python --version)" "$(which python3)"

printf "%s: running tests\\n" "$LOG_PREFIX"
python3 -m tox


printf "%s: size of pre-push tmp dir:\\n" "$LOG_PREFIX"
du -h $PWD | sort -h | tail -n 7

printf "%s: DONE AOK\\n" "$LOG_PREFIX"
exit 0
