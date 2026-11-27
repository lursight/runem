import typing
from concurrent.futures import Future
from contextlib import contextmanager

from runem.report.metrics.time_entry_recorder import RecordTimeEntryFn
from runem.report.metrics.timed_context import timed_context
from runem.report.metrics.timing_info import TimeInfo


@contextmanager
def timed_context_callback(
    label: str,
    record_time_entry_cb: typing.Optional[RecordTimeEntryFn],
) -> typing.Generator[None, None, None]:
    if record_time_entry_cb is None:
        yield  # we can't time anything
        return

    time_info_future: typing.Optional[Future[TimeInfo]] = None
    try:
        with timed_context() as time_info_future:
            yield  # run the thing that is being timed
    finally:
        # Always *attempt* to resolve some info.
        if time_info_future is not None:
            time_info: TimeInfo = time_info_future.result()
            record_time_entry_cb(label, time_info)
