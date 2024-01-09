import os
import pathlib
import sys
import typing

import pytest

FixtureRequest = typing.Any


# each test runs on cwd to its temp dir
@pytest.fixture(autouse=True)
def go_to_tmp_path(request: FixtureRequest) -> typing.Generator[None, None, None]:
    # Get the fixture dynamically by its name.
    tmp_path: pathlib.Path = request.getfixturevalue("tmp_path")
    # ensure local test created packages can be imported
    sys.path.insert(0, str(tmp_path))
    # Chdir only for the duration of the test.
    origin = pathlib.Path().absolute()
    try:
        os.chdir(tmp_path)
        yield
    finally:
        os.chdir(origin)
