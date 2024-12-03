import time
import typing

from rich.console import Console


def _reset_console() -> Console:
    """Sets the nice user-facing console.

    This function exists so we can reset the output from tests.
    """
    global RICH_CONSOLE  # pylint: disable=global-statement

    RICH_CONSOLE = Console(log_path=False)
    return RICH_CONSOLE


# Overridden in tests.
RICH_CONSOLE: Console = _reset_console()


def _reset_console_for_tests() -> None:
    """Overrides the console output with more deterministic version.

    ... so we can have deterministic tests.
    """
    global RICH_CONSOLE  # pylint: disable=global-statement
    RICH_CONSOLE = Console(log_path=False, log_time=False, width=999)


def blocking_print(
    msg: str = "",
    end: typing.Optional[str] = None,
    max_retries: int = 5,
    sleep_time_s: float = 0.1,
) -> None:
    """Attempt to print a message, retrying on BlockingIOError.

    Sometimes in long-lasting jobs, that produce lots of output, we hit
    BlockingIOError where we can't print to screen because the buffer is full or
    already being written to (for example), i.e. the `print` would need to be a
    'blocking' call, which it is not.
    """
    if end is None:
        end = "\n"
    for _ in range(max_retries):
        try:
            RICH_CONSOLE.print(msg, end=end)
            break  # Success, exit the retry loop
        except BlockingIOError:
            time.sleep(sleep_time_s)  # Wait a bit for the buffer to clear
    else:
        # Optional: handle the failure to print after all retries
        pass
