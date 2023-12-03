import io
import pathlib
from collections import defaultdict
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from runem.runem import timed_main
from runem.types import Config, GlobalSerialisedConfig


def test_runem_basic() -> None:
    """Tests new user's first call-path, when they wouldn't have a .runem.yml."""
    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(SystemExit):
            timed_main([])
        runem_stdout = buf.getvalue()

        # this is what we should see when first installing runem
        # TODO: add an on-boarding work flow
        assert "ERROR: Config not found! Looked from" in runem_stdout


@patch(
    "runem.runem.load_config",
)
@patch(
    "runem.runem.find_files",
)
def test_runem_basic_with_config(
    find_files_mock: Mock,
    load_config_mock: Mock,
) -> None:
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("mock phase",),
            "files": [],
            "options": [],
        }
    }
    empty_config: Config = [
        global_config,
    ]
    minimal_file_lists = defaultdict(list)
    minimal_file_lists["mock phase"].append(pathlib.Path("/test") / "dummy" / "path")
    load_config_mock.return_value = (empty_config, pathlib.Path())
    find_files_mock.return_value = minimal_file_lists
    with io.StringIO() as buf, redirect_stdout(buf):
        # with pytest.raises(SystemExit):
        timed_main(["--help"])
        runem_stdout = buf.getvalue().split("\n")
        assert [
            "found 1 batches, 1 'mock phase' files, ",
            "filtering for tags set()",
            "skipping phase 'mock phase'",
        ] == runem_stdout[:3]
