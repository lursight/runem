import os
import pathlib
import sys

import pytest


# each test runs on cwd to its temp dir
@pytest.fixture(autouse=True)
def go_to_tmp_path(request):
    # Get the fixture dynamically by its name.
    tmp_path: pathlib.Path = request.getfixturevalue("tmp_path")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmp_path))
    # Chdir only for the duration of the test.
    with os.chdir(tmp_path):
        yield
