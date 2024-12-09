# SPDX-FileCopyrightText: © 2021 Frank Harrison <frank@doublethefish.com>, all rights reserved
# SPDX-License-Identifier: BSD-3-Clause

# exit when any command fails
set -e

LOG_PREFIX="runem: pre-push: branch:"

function RUN_LABELED_CMD {
  # Run a command, changing the output such that it is prefixed by "LABEL"
  LABEL=$1
  CMD="${@:2}"

  $CMD 2>&1 | sed -e 's/^/'"$LABEL"': /g'
  EXIT_CODE=$?
  return $EXIT_CODE
}

# Get the root-checkout path of runem:
RUNEM_CHECKOUT=$(runem --root-show | grep -v "runem: ")
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
printf "%s cloning to %s\\n" "$LOG_PREFIX" "$PRE_PUSH_TEST_DIR"
printf "%s clone-size is %s, %s\\n" "$LOG_PREFIX" "$(du -sh $MDGM_LURSIGHT_CHECKOUT/.git)" "$(du -sh $MDGM_LURSIGHT_CHECKOUT/.pyenv)"

mkdir -p "$PRE_PUSH_TEST_DIR"

cd "$PRE_PUSH_TEST_DIR"
# if the dir exists already clean files that are untracked but NOT in .gitignore
# NOTE: This partially supports NO_CLEAN=1 by ensuring a minimal clean up is performed
#       before rsync.
# RUN_LABELED_CMD "mdgm-lursight: pre-push: initial tmp-dir cleanup" git clean -fd || true

# copy over _just_ the .git dir
rsync -vhlpr --delete-before "$RUNEM_CHECKOUT"/.git "$PRE_PUSH_TEST_DIR/" || exit 44
