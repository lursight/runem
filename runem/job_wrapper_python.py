import pathlib
import sys
from importlib.util import module_from_spec
from importlib.util import spec_from_file_location as module_spec_from_file_location

from runem.types.errors import FunctionNotFound
from runem.types.runem_config import JobWrapper
from runem.types.types_jobs import JobFunction


def _load_python_function_from_module(
    cfg_filepath: pathlib.Path,
    module_name: str,
    module_file_path: pathlib.Path,
    function_to_load: str,
) -> JobFunction:
    """Given a job-description dynamically loads the test-function so we can call it."""

    # first locate the module relative to the config file
    abs_module_file_path: pathlib.Path = (
        cfg_filepath.parent / module_file_path
    ).absolute()

    # load the function
    try:
        module_spec = module_spec_from_file_location(
            function_to_load, abs_module_file_path
        )
        if not module_spec:
            raise FileNotFoundError()
        if not module_spec.loader:  # pragma: FIXME: add code coverage
            raise FunctionNotFound("unable to load module")
    except FileNotFoundError as err:
        raise FunctionNotFound(
            (
                f"unable to load '{function_to_load}' from '{str(module_file_path)} "
                f"relative to '{str(cfg_filepath)}"
            )
        ) from err

    module = module_from_spec(module_spec)
    if not module:
        raise FunctionNotFound("unable to load module")
    sys.modules[module_name] = module
    try:
        module_spec.loader.exec_module(module)
    except FileNotFoundError as err:
        raise FunctionNotFound(
            (
                f"unable to load '{function_to_load}' from '{str(module_file_path)} "
                f"relative to '{str(cfg_filepath)}"
            )
        ) from err
    try:
        function: JobFunction = getattr(module, function_to_load)
    except AttributeError as err:
        raise FunctionNotFound(
            (
                f"ERROR! Check that function '{function_to_load}' "
                f"exists in '{str(module_file_path)}' as expected in "
                f"your config at '{str(cfg_filepath)}"
            )
        ) from err
    return function


def _find_job_module(cfg_filepath: pathlib.Path, module_file_path: str) -> pathlib.Path:
    """Attempts to find the true location of the job-function module."""
    module_path: pathlib.Path = pathlib.Path(module_file_path)

    module_path_candidates = [
        module_path,
        module_path.absolute(),
        (cfg_filepath.parent / module_file_path).absolute(),
    ]
    for module_path in module_path_candidates:
        if module_path.exists():
            break
    if not module_path.exists():
        raise FunctionNotFound(
            (
                f"unable to find test-function module looked in {module_path_candidates} "
                f"running from '{pathlib.Path('.').absolute()}'"
            )
        )
    module_path = module_path.absolute()
    return module_path.relative_to(cfg_filepath.parent.absolute())


def get_job_wrapper_py_func(
    job_wrapper: JobWrapper, cfg_filepath: pathlib.Path
) -> JobFunction:
    """For a job, dynamically loads the associated python job-function.

    Side-effects: also re-addressed the job-config.
    """
    function_to_load: str = job_wrapper["addr"]["function"]
    try:
        module_file_path: pathlib.Path = _find_job_module(
            cfg_filepath, job_wrapper["addr"]["file"]
        )
    except FunctionNotFound as err:
        raise FunctionNotFound(
            (
                "runem failed to find "
                f"job.addr.file '{job_wrapper['addr']['file']}' looking for "
                f"job.addr.function '{function_to_load}'"
            )
        ) from err

    anchored_file_path = cfg_filepath.parent / module_file_path
    assert (
        anchored_file_path.exists()
    ), f"{module_file_path} not found at {anchored_file_path}!"

    module_name = module_file_path.stem.replace(" ", "_").replace("-", "_")

    function = _load_python_function_from_module(
        cfg_filepath, module_name, module_file_path, function_to_load
    )

    # re-write the job-config file-path for the module with the one that worked
    job_wrapper["addr"]["file"] = str(module_file_path)
    return function
