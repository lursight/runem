import pathlib
import shutil
from unittest.mock import Mock, patch

import pytest

from runem.job_function_python import (
    _load_python_function_from_module,
    get_job_function,
)
from runem.types import FunctionNotFound, JobConfig, JobFunction


def test_get_job_function(tmp_path: pathlib.Path) -> None:
    """Tests that loading a function works.

    The files have to be in the same path and we use the tmp_path so we copy the right
    files there.
    """
    source_file = pathlib.Path(__file__)
    copied_py = tmp_path / source_file.name
    shutil.copyfile(source_file, copied_py)

    job_config: JobConfig = {
        "addr": {
            "file": str(copied_py),
            "function": "test_get_job_function",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "py",
                    "format",
                )
            ),
        },
    }
    loaded_func: JobFunction = get_job_function(job_config, tmp_path / ".runem.yml")
    assert loaded_func is not None
    assert loaded_func.__name__ == "test_get_job_function"


def test_get_job_function_handles_missing_function(tmp_path: pathlib.Path) -> None:
    """Tests that loading a non-existent function in a valid file fails gracefully.

    The files have to be in the same path and we use the tmp_path so we copy the right
    files there.
    """
    source_file = pathlib.Path(__file__)
    copied_py = tmp_path / source_file.name
    shutil.copyfile(source_file, copied_py)

    job_config: JobConfig = {
        "addr": {
            "file": str(copied_py),
            "function": "function_does_not_exist",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "py",
                    "format",
                )
            ),
        },
    }

    with pytest.raises(FunctionNotFound):
        # this should throw an exception
        get_job_function(job_config, tmp_path / ".runem.yml")


def test_get_job_function_handles_missing_module(tmp_path: pathlib.Path) -> None:
    """Tests that loading a non-existent function in a valid file fails gracefully.

    The files have to be in the same path and we use the tmp_path so we copy the right
    files there.
    """
    source_file = pathlib.Path(__file__)
    not_copied_py = tmp_path / source_file.name

    job_config: JobConfig = {
        "addr": {
            "file": str(not_copied_py),
            "function": "function_does_not_exist",
        },
        "label": "reformat py",
        "when": {
            "phase": "edit",
            "tags": set(
                (
                    "py",
                    "format",
                )
            ),
        },
    }

    with pytest.raises(FunctionNotFound):
        # this should throw an exception
        get_job_function(job_config, tmp_path / ".runem.yml")


@patch(
    "runem.job_function_python.module_spec_from_file_location",
    return_value=None,
)
def test_load_python_function_from_module_handles_module_spec_loading(
    mock_spec_from_file_location: Mock,
) -> None:
    """Tests that the importlib internals failing to load a module-spec is handled.

    mocks importlib.util.spec_from_file_location to return None
    """
    file_path: pathlib.Path = pathlib.Path(__file__)
    base_path = file_path.parent
    with pytest.raises(FunctionNotFound) as err_info:
        _load_python_function_from_module(
            base_path / ".rune.no_exist.yml",
            "test_module_name",
            file_path,
            "test_load_python_function_from_module_handles_module_spec_loading",
        )
    assert str(err_info.value).startswith(
        (
            "unable to load "
            "'test_load_python_function_from_module_handles_module_spec_loading' from"
        )
    )
    mock_spec_from_file_location.assert_called()
