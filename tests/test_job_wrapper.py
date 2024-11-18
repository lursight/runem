import pathlib
from unittest.mock import Mock, patch

from runem import job_runner_simple_command
from runem.job_wrapper import get_job_wrapper
from runem.types.runem_config import JobConfig
from runem.types.types_jobs import JobFunction

DUMMY_FUNCTION: JobFunction = (
    "intentionally bad type as string to test call"  # type: ignore[assignment]
)


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
        job_config, cfg_filepath=pathlib.Path(__file__)
    )
    assert func_obj == DUMMY_FUNCTION

    # with a python-function job-config if should call the mock once
    mock_get_job_wrapper_py_func.assert_called_once()


@patch(
    "runem.job_wrapper.get_job_wrapper_py_func",
    return_value=None,
)
def test_get_job_wrapper_simple_command_job(mock_get_job_wrapper_py_func: Mock) -> None:
    """Checks that the job_runner_simple_command is returned for 'command' jobs."""
    job_config: JobConfig = {
        "command": "echo 'testing exec'",
    }
    func_obj: JobFunction = get_job_wrapper(
        job_config, cfg_filepath=pathlib.Path(__file__)
    )

    assert func_obj.__name__ == job_runner_simple_command.__name__.split(".")[1]

    # with simple jobs the python wrapper lookup should NOT be called.
    mock_get_job_wrapper_py_func.assert_not_called()
