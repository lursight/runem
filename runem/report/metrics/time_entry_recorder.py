# A function type for recording timing information.
import typing

from runem.report.metrics.timing_info import TimeInfo

RecordTimeEntryFn = typing.Callable[[str, TimeInfo], None]
