import os
import pathlib
import sys
import typing

import pytest

from runem.blocking_print import _reset_console, _reset_console_for_tests

FixtureRequest = typing.Any


@pytest.fixture(autouse=True)
def use_test_rich_print(request: FixtureRequest) -> typing.Generator[None, None, None]:
    """Each test should use the test-version of the `rich` print function.

    This is so we get deterministic output with out timestamps nor auto-wrapping console
    output.
    """
    _reset_console_for_tests()
    yield
    _reset_console()


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
