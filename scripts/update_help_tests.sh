set -e

SCRIPT_PATH="$(realpath "$0")"
DIR_PATH="$(dirname "$SCRIPT_PATH")"

# Updates the help tests for the major version of python that contain changes to
# things like argsparse etc.
bash "$DIR_PATH/update_help_tests_for_python.sh" 3.9
bash "$DIR_PATH/update_help_tests_for_python.sh" 3.11