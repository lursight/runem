import typing
from concurrent.futures import Future
from contextlib import contextmanager
from dataclasses import dataclass

from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.time_entry import TimedEntries, TimeEntry
from runem.report.metrics.time_entry_recorder import RecordTimeEntryFn
from runem.report.metrics.timed_context import timed_context
from runem.report.metrics.timing_info import TimeInfo


@dataclass(frozen=True)
class JobTimingContext:
    """Context-specific JobTiming info.

    As we cannot construct the JobTiming until
    `__exit__` we [mis]user concurrent concurrent.futures to
    indicate readiness of concrete value.
    """

    future: Future[JobTiming]
    record_sub_job_time_cb: RecordTimeEntryFn


@contextmanager
def timed_job_context(
    label: str,
) -> typing.Generator[JobTimingContext, None, None]:
    sub_command_timings: TimedEntries = []

    def _record_sub_job_time(label: str, time_info: TimeInfo) -> None:
        """Record timing information for sub-commands/tasks, atomically.

        For example inside of run_command() calls
        """
        sub_command_timings.append(TimeEntry(label=label, info=time_info))

    job_timing_context = JobTimingContext(
        future=Future(),
        record_sub_job_time_cb=_record_sub_job_time,
    )
    time_info_future: typing.Optional[Future[TimeInfo]] = None
    try:
        with timed_context() as time_info_future:
            # Yield the context with the Future and the call-back
            yield job_timing_context  # run the thing that is being timed
    finally:
        # Always *attempt* to resolve some info.
        if time_info_future is not None:
            time_info: TimeInfo = time_info_future.result()
            time_entry = TimeEntry(label=label, info=time_info)
            job_timing = JobTiming(job=time_entry, commands=sub_command_timings)
            job_timing_context.future.set_result(job_timing)
