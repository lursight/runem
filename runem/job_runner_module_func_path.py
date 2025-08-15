import importlib
import os
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
    except (  # noqa: B014
        ModuleNotFoundError,  # known/seen error
        Exception,  # We do not yet know the full range of exceptions, for now
    ) as err:  # pylint: disable=broad-except
        indented_orig_err: str = str(err).replace("\n", "\n\t")
        raise FunctionNotFound(
            f"Unable to import module '{mod_path}' from dotted path "
            f"'{module_func_path}'. \n"
            f"Check the PYTHONPATH and installed packages; "
            f"\n\tconfig at '{cfg_filepath}'"
            f"\n\tcwd is {pathlib.Path.cwd()}"
            f"\n\tPYTHONPATH is '{os.environ.get('PYTHONPATH', '')}'"
            "\nOriginal error is:"
            f"\n\t{indented_orig_err}"
            "\nIn your cwd try:"
            f'\n\tpython3 -c "import {mod_path}"'
        ) from err

    try:
        func: JobFunction = getattr(module, func_name)
    except AttributeError as err:
        raise FunctionNotFound(
            f"Function '{func_name}' not found in module '{mod_path}'."
            f"Confirm it exists and is exported, checking the job's `cwd`; "
            f"\n\tconfig at '{cfg_filepath}'\n\tcwd is {pathlib.Path.cwd()}\n"
            f"\n\tcwd is {pathlib.Path.cwd()}"
            f"\n\tPYTHONPATH is '{os.environ.get('PYTHONPATH', '')}'"
            "\nIn your cwd try:"
            f'\n\tpython3 -c "from {mod_path} import {func_name}"'
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
        err_message: str = (
            "runem failed to find "
            f"job.module '{job_wrapper['module']}' from '{cfg_filepath}'\n"
            "Original error is:\n"
            f"{str(err)}"
        )
        raise FunctionNotFound(err_message) from err

    return function
