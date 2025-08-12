import io
from contextlib import redirect_stdout
from pathlib import Path

from typing_extensions import Unpack

from runem.job_runner_module_func_path import (
    _load_python_function_from_dotted_path,
)
from runem.types.types_jobs import JobFunction, JobKwargs
from tests.utils.dummy_data import DUMMY_JOB_K_ARGS

DOT_PATH_THIS_FILE = "tests.test_job_runner_module_func_path"


def dummy_job_function_no_params(**kwargs: Unpack[JobKwargs]) -> None:
    """A simple callable used for positive-path testing."""
    print("dummy job function no params")


def test_load_function_success() -> None:
    """Loads a real callable from this test module."""
    func: JobFunction = _load_python_function_from_dotted_path(
        cfg_filepath=Path(__file__),
        module_func_path=f"{DOT_PATH_THIS_FILE}.dummy_job_function_no_params",
    )
    with io.StringIO() as buf, redirect_stdout(buf):
        func(**DUMMY_JOB_K_ARGS)
        stdout: str = buf.getvalue()
    stdout_lines = stdout.split("\n")
    assert stdout_lines == [
        "dummy job function no params",
        "",
    ]
