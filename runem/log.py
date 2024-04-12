import typing

from runem.blocking_print import blocking_print


def log(msg: str = "", decorate: bool = True, end: typing.Optional[str] = None) -> None:
    """Thin wrapper around 'print', change the 'msg' & handles system-errors.

    One way we change it is to decorate the output with 'runem'
    """
    if decorate:
        msg = f"runem: {msg}"

    # print in a blocking manner, waiting for system resources to free up if a
    # runem job is contending on stdout or similar.
    blocking_print(msg, end=end)


def warn(msg: str) -> None:
    log(f"WARNING: {msg}")


def error(msg: str) -> None:
    log(f"ERROR: {msg}")
