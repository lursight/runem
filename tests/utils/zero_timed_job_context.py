"""A deterministic job-timing context for tests that do not measure elapsed time."""

import typing
from concurrent.futures import Future
from contextlib import contextmanager

from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.time_entry import TimeEntry
from runem.report.metrics.timed_job_context import JobTimingContext
from runem.report.metrics.timing_info import TimeInfo


@contextmanager
def zero_timed_job_context(
    label: str,
) -> typing.Generator[JobTimingContext, None, None]:
    """Keep job timing fixed at zero and preserve recorded command entries."""
    command_timings: typing.List[TimeEntry] = []
    timing_future: Future[JobTiming] = Future()

    def record_command(label: str, time_info: TimeInfo) -> None:
        command_timings.append(TimeEntry(label=label, info=time_info))

    timing_context = JobTimingContext(
        future=timing_future,
        record_sub_job_time_cb=record_command,
    )
    try:
        yield timing_context
    finally:
        timing_future.set_result(
            JobTiming(
                job=TimeEntry(
                    label=label,
                    info=TimeInfo(start=0, end=0),
                ),
                commands=command_timings,
            )
        )
