import typing
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class TimingEntry:
    """A time-profiling entry."""

    label: str
    dur: timedelta


TimingEntries = typing.List[TimingEntry]
