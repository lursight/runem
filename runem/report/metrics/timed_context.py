"""TimeInfo capturing context-manager.

Useful for general timing capture

To bind to runem's analysis and reporting systems see
the other `timed_context_X` utils.
"""

import typing
from concurrent.futures import Future
from contextlib import contextmanager
from timeit import default_timer as timer

from runem.report.metrics.timing_info import TimeInfo


@contextmanager
def timed_context() -> typing.Generator[Future[TimeInfo], None, None]:
    """Context-manager that captures TimeInfo for the context-window.

    Example use:
        with timed_context() as time_info_future:
            # .. do work
        time_info: TimeInfo = time_info_future.result()

    Yields:
        Future[TimeInfo] which resolves at context.__exit__.
    """
    result: Future[TimeInfo] = Future()
    start = timer()

    try:
        yield result  # run the thing that is being timed
    finally:
        # Always attempt to resolve some info, because:
        # - We're using `concurrent.Future` so it's
        #   less surprising if we can try to resolve
        #   some timing information, even in failure
        #   cases.
        # - User experience is also more wholistic and
        #   informed as we can report as much
        #   information as possible, even when it's
        #   not reflective of the 'working state'.
        # Capture how long this run took
        end = timer()
        result.set_result(TimeInfo(start=start, end=end))
