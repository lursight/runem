from __future__ import annotations

import io
import types
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

import pytest
from typing_extensions import Unpack

from runem.job_runner_module_func_path import (
    _load_python_function_from_dotted_path,
    get_job_wrapper_py_module_dot_path,
)
from runem.types.errors import FunctionNotFound
from runem.types.runem_config import JobWrapper
from runem.types.types_jobs import JobFunction, JobKwargs
from tests.utils.dummy_data import DUMMY_JOB_K_ARGS

DOT_PATH_THIS_FILE = "tests.test_job_runner_module_func_path"


def dummy_job_function_no_params(**kwargs: Unpack[JobKwargs]) -> None:
    """A simple callable used for positive-path testing."""
    print("dummy job function no params")


# ---------- Positive paths ----------


def test_load_function_success() -> None:
    """Loads a real callable from this test module."""
    func: JobFunction = _load_python_function_from_dotted_path(
        cfg_filepath=Path(__file__),
        module_func_path=f"{DOT_PATH_THIS_FILE}.dummy_job_function_no_params",
    )
    assert callable(func)
    assert func is dummy_job_function_no_params  # type: ignore[comparison-overlap]

    with io.StringIO() as buf, redirect_stdout(buf):
        func(**DUMMY_JOB_K_ARGS)
        stdout: str = buf.getvalue()
    stdout_lines = stdout.split("\n")
    assert stdout_lines == [
        "dummy job function no params",
        "",
    ]


def test_get_job_wrapper_success() -> None:
    """get_job_wrapper_py_module_dot_path returns the same callable on success."""
    job_wrapper: JobWrapper = {
        "module": f"{DOT_PATH_THIS_FILE}.dummy_job_function_no_params"
    }
    func: JobFunction = get_job_wrapper_py_module_dot_path(
        job_wrapper=job_wrapper,
        cfg_filepath=Path(__file__),
    )
    assert func is dummy_job_function_no_params  # type: ignore[comparison-overlap]

    with io.StringIO() as buf, redirect_stdout(buf):
        func(**DUMMY_JOB_K_ARGS)
        stdout: str = buf.getvalue()
    stdout_lines = stdout.split("\n")
    assert stdout_lines == [
        "dummy job function no params",
        "",
    ]


# ---------- Invalid dotted path variants ----------


@pytest.mark.parametrize(
    "bad_path",
    [
        "",  # empty
        "abc",  # no dot separator
        "abc.",  # missing function name
        ".func",  # missing module path
    ],
)
def test_invalid_dotted_path_raises(bad_path: str) -> None:
    """Invalid dotted strings are rejected early with FunctionNotFound."""
    with pytest.raises(FunctionNotFound) as ei:
        _ = _load_python_function_from_dotted_path(
            cfg_filepath=Path("cfg.yml"),
            module_func_path=bad_path,
        )
    # Helpful, deterministic message (keeps stoic clarity for users)
    assert "Invalid dotted path" in str(ei.value)


# ---------- Import failure (module cannot be imported) ----------


def test_import_failure_wraps_as_function_not_found() -> None:
    """Non-existent module should bubble up as FunctionNotFound with context."""
    with pytest.raises(FunctionNotFound) as ei:
        _ = _load_python_function_from_dotted_path(
            cfg_filepath=Path("cfg.yml"),
            module_func_path="this.module.does.not.exist.func",
        )
    assert "Unable to import module" in str(ei.value)


# ---------- Attribute missing on imported module ----------


def test_attribute_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module imports, but attribute is absent -> FunctionNotFound."""
    mod_name = "tmp_attr_missing_mod"
    module = types.ModuleType(mod_name)
    monkeypatch.setitem(__import__("sys").modules, mod_name, module)

    with pytest.raises(FunctionNotFound) as ei:
        _ = _load_python_function_from_dotted_path(
            cfg_filepath=Path("cfg.yml"),
            module_func_path=f"{mod_name}.nope",
        )
    assert "Function 'nope' not found" in str(ei.value)


# ---------- Attribute exists but is not callable ----------


def test_attribute_not_callable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module has the attribute, but it's not callable -> FunctionNotFound."""
    mod_name = "tmp_not_callable_mod"
    module = types.ModuleType(mod_name)
    module.not_callable: Any = 123  # type: ignore[attr-defined,misc]
    monkeypatch.setitem(
        __import__("sys").modules,
        mod_name,
        module,
    )

    with pytest.raises(FunctionNotFound) as ei:
        _ = _load_python_function_from_dotted_path(
            cfg_filepath=Path("cfg.yml"),
            module_func_path=f"{mod_name}.not_callable",
        )
    assert "is not callable" in str(ei.value)


# ---------- Wrapper re-raises with runem-flavoured message ----------


def test_get_job_wrapper_rewraps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrapper should reword FunctionNotFound with job.module context."""
    mod_name = "tmp_wrapper_bad"
    # Ensure the module is truly absent so import fails
    sys_mods = __import__("sys").modules
    sys_mods.pop(mod_name, None)

    job_wrapper: JobWrapper = {"module": f"{mod_name}.missing"}
    with pytest.raises(FunctionNotFound) as ei:
        get_job_wrapper_py_module_dot_path(
            job_wrapper=job_wrapper,
            cfg_filepath=Path("cfg.yml"),
        )
    msg = str(ei.value)
    assert "runem failed to find job.module" in msg
    assert f"'{job_wrapper['module']}'" in msg
