import pathlib
import shutil
from unittest.mock import Mock, patch

import pytest

from runem.job_wrapper_python import (
    _load_python_function_from_module,
    get_job_wrapper_py_func,
)
from runem.types.errors import FunctionNotFound
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import JobFunction


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
    loaded_func: JobFunction = get_job_wrapper_py_func(
        job_config, tmp_path / ".runem.yml"
    )
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
        get_job_wrapper_py_func(job_config, tmp_path / ".runem.yml")


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
        get_job_wrapper_py_func(job_config, tmp_path / ".runem.yml")


@patch(
    "runem.job_wrapper_python.module_spec_from_file_location",
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
            base_path / ".runem.no_exist.yml",
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


@patch(
    "runem.job_wrapper_python.module_from_spec",
    return_value=None,
)
def test_load_python_function_from_module_handles_module_from_spec_failing(
    mock_module_from_spec: Mock,
) -> None:
    """Tests that another case of importlib internals failing is handled.

    mocks importlib.util.module_from_spec to return None
    """
    file_path: pathlib.Path = pathlib.Path(__file__)
    base_path = file_path.parent
    with pytest.raises(FunctionNotFound, match=("unable to load module")):
        _load_python_function_from_module(
            base_path / ".runem.no_exist.yml",
            "test_module_name",
            file_path,
            "test_load_python_function_from_module_handles_module_spec_loading",
        )
    mock_module_from_spec.assert_called()


def test_load_python_function_success(tmp_path: pathlib.Path) -> None:
    # Create a temporary Python module file
    p = tmp_path / "hello.py"
    p.write_text('def hello():\n    return "Hello, World!"')

    # Use the function to load the module and retrieve the function
    hello_func = _load_python_function_from_module(
        p, "hello_module", pathlib.Path("hello.py"), "hello"
    )

    # True if the function can be called and returns expected result
    assert callable(hello_func)
    assert hello_func() == "Hello, World!"  # type: ignore


def test_load_python_function_module_not_found(tmp_path: pathlib.Path) -> None:
    # Use the function to load a non-existing module
    with pytest.raises(FunctionNotFound):
        _load_python_function_from_module(
            tmp_path, "not_found_module", pathlib.Path("not_found.py"), "not_found"
        )


def test_load_python_function_not_found(tmp_path: pathlib.Path) -> None:
    # Create a temporary Python module file
    p = tmp_path / "hello.py"
    p.write_text(
        """
    def hello():
        return "Hello, World!"
    """
    )

    # Use the function to load the module but try to retrieve a non-existent function
    with pytest.raises(FunctionNotFound):
        _load_python_function_from_module(
            tmp_path, "hello_module", pathlib.Path("hello.py"), "not_found"
        )


def test_load_python_function_invalid_module(tmp_path: pathlib.Path) -> None:
    # Create an invalid Python module file
    p = tmp_path / "invalid.py"
    p.write_text(
        """
    def 123invalid():
        return "Invalid!"
    """
    )

    # Use the function to load the invalid module and expect a FunctionNotFound exception
    with pytest.raises(FunctionNotFound):
        _load_python_function_from_module(
            tmp_path, "invalid_module", pathlib.Path("invalid.py"), "123invalid"
        )
