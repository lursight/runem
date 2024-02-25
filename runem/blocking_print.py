import time
import typing


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
    for _ in range(max_retries):
        try:
            print(msg, end=end)
            break  # Success, exit the retry loop
        except BlockingIOError:
            time.sleep(sleep_time_s)  # Wait a bit for the buffer to clear
    else:
        # Optional: handle the failure to print after all retries
        pass
