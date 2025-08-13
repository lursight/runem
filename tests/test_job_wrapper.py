import pathlib
from unittest.mock import ANY, Mock, patch

from runem.job_wrapper import get_job_wrapper
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import JobFunction

# use a string as a ad type to test call
DUMMY_FUNCTION: JobFunction = "intentionally bad type"  # type: ignore[assignment]


@patch(
    "runem.job_wrapper.get_job_wrapper_py_func",
    return_value=DUMMY_FUNCTION,
)
def test_get_job_wrapper_python_wrapper_job(mock_get_job_wrapper_py_func: Mock) -> None:
    """Checks that the python wrapper job lookup is called."""
    job_config: JobConfig = {
        "addr": {
            "file": __file__,
            "function": "test_get_job_wrapper",
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
    func_obj: JobFunction = get_job_wrapper(
        job_config,
        cfg_filepath=pathlib.Path(__file__),
    )
    assert func_obj == DUMMY_FUNCTION

    # with a python-function job-config if should call the mock once
    mock_get_job_wrapper_py_func.assert_called_once()


@patch(
    "runem.job_wrapper.get_job_wrapper_py_func",
    return_value=None,
)
@patch(
    "runem.job_wrapper.get_job_wrapper_py_module_dot_path",
    return_value="dummy func",
)
def test_get_job_wrapper_module_path(
    mock_get_job_wrapper_py_module_dot_path: Mock,
    mock_get_job_wrapper_py_func: Mock,
) -> None:
    """Checks that the correct  is returned for 'command' jobs."""
    job_config: JobConfig = {
        "module": "does.not.matter.the.path.to.fn",
    }
    func_obj: JobFunction = get_job_wrapper(
        job_config,
        cfg_filepath=pathlib.Path(__file__),
    )

    assert func_obj == "dummy func"  # type: ignore[comparison-overlap]
    # with simple jobs the python wrapper lookup should NOT be called.
    mock_get_job_wrapper_py_func.assert_not_called()
    mock_get_job_wrapper_py_module_dot_path.assert_called_once_with(
        {"module": "does.not.matter.the.path.to.fn"},
        ANY,
    )
