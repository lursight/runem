set -e

# pull the version from the command-line
PYTHON_VERSION=$1

# Get the help-tests to rebuild their content
export RUNEM_UPDATE_HELP_TESTS=1

# try deactivate the current v-env (if active)
deactivate || true
# try and delete the dir containing it (if exists)
rm -rf .pyenv || true

# Use the requested verion and configure the v-env
pyenv local "$PYTHON_VERSION"
python3 -m virtualenv .pyenv -p python3 
source .pyenv/bin/activate
python3 -m pip install -e '.[test]' 

# Run the tests in the new environ
python3 -m runem.runem 