import typing
from contextlib import contextmanager
from datetime import timedelta
from timeit import default_timer as timer

# A function type for recording timing information.
RecordSubJobTimeType = typing.Callable[[str, timedelta], None]


@contextmanager
def runem_timer(
    label: str,
    record_sub_job_time: typing.Optional[RecordSubJobTimeType],
) -> typing.Iterator[None]:
    if record_sub_job_time is None:
        yield  # we can't time anything
        return

    start = timer()

    yield  # run the thing that is being timed

    # Capture how long this run took
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    record_sub_job_time(label, time_taken)
