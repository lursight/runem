import typing

from runem.blocking_print import blocking_print


def log(
    msg: str = "",
    decorate: bool = True,
    end: typing.Optional[str] = None,
) -> None:
    """Thin wrapper around 'print', change the 'msg' & handles system-errors.

    One way we change it is to decorate the output with 'runem'

    Parameters:
        msg: str - the message to log out. Any `rich` markup will be escaped
                   and not applied.
        decorate: str - whether to add runem-specific prefix text. We do this
                        to identify text that comes from the app vs text that
                        comes from hooks or other third-parties.
        end: Optional[str] - same as the end option used by `print()` and
                             `rich`
    Returns:
        Nothing
    """
    # Remove any markup as it will probably error, if unsanitised.
    # msg = escape(msg)

    if decorate:
        # Make it clear that the message comes from `runem` internals.
        msg = f"runem: {msg}"

    # print in a blocking manner, waiting for system resources to free up if a
    # runem job is contending on stdout or similar.
    blocking_print(msg, end=end)


def warn(msg: str) -> None:
    log(f"WARNING: {msg}")


def error(msg: str) -> None:
    log(f"ERROR: {msg}")
