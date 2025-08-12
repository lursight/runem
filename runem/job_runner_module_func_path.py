import importlib
import pathlib

from runem.types.errors import FunctionNotFound
from runem.types.runem_config import JobWrapper
from runem.types.types_jobs import JobFunction


def _load_python_function_from_dotted_path(
    cfg_filepath: pathlib.Path,
    module_func_path: str,
) -> JobFunction:
    """Load a Python function given a dotted path like 'pkg.module.func'.

    Args:
            cfg_filepath: Path to the config file (used only for clearer error messages).
            module_func_path: Dotted path to the target function, e.g. 'a.b.c.my_func'.

    Returns:
            The imported callable.

    Raises:
            FunctionNotFound: If the module cannot be imported or the attribute is
                              missing/not callable.
    z
        Example:
            >>> fn = _load_python_function_from_dotted_path(Path('cfg.yml'), 'my_mod.tasks.run')
            >>> fn()  # call it
    """
    mod_path, sep, func_name = module_func_path.rpartition(".")
    if not sep or not mod_path or not func_name:
        raise FunctionNotFound(
            f"Invalid dotted path '{module_func_path}'. Expected format 'pkg.module.func'. "
            f"Check your config at '{cfg_filepath}'."
        )

    try:
        module = importlib.import_module(mod_path)
    except Exception as err:  # pylint: disable=broad-except
        raise FunctionNotFound(
            f"Unable to import module '{mod_path}' from dotted path '{module_func_path}'. "
            f"Check PYTHONPATH and installed packages; config at '{cfg_filepath}'."
        ) from err

    try:
        func: JobFunction = getattr(module, func_name)
    except AttributeError as err:
        raise FunctionNotFound(
            f"Function '{func_name}' not found in module '{mod_path}'. "
            f"Confirm it exists and is exported; config '{cfg_filepath}'."
        ) from err

    if not callable(func):
        raise FunctionNotFound(
            f"Attribute '{func_name}' in module '{mod_path}' is not callable. "
            f"Update your config '{cfg_filepath}' to reference a function."
        )
    return func


def get_job_wrapper_py_module_dot_path(
    job_wrapper: JobWrapper,
    cfg_filepath: pathlib.Path,
) -> JobFunction:
    """For a job, dynamically loads the associated python job-function.

    Side-effects: also re-addressed the job-config.
    """
    function_path_to_load: str = job_wrapper["module"]
    try:
        function: JobFunction = _load_python_function_from_dotted_path(
            cfg_filepath, function_path_to_load
        )
    except FunctionNotFound as err:
        raise FunctionNotFound(
            (
                "runem failed to find "
                f"job.module '{job_wrapper['module']}' from '{cfg_filepath}'"
            )
        ) from err

    return function
