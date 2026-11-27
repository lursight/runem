"""An analysis, visualisation and data-lookup time-entry.

TimedEntry is designed:
      > .. to be a labeled, context-aware entry.
      > .. to be used for:
          - visualisations
          - analysis
          - other data-lookups.
"""

import typing
from dataclasses import dataclass

from runem.report.metrics.timing_info import TimeInfo


@dataclass(frozen=True)
class TimeEntry:
    """A time entry.

    Used for labelled, timing events.

    Designed to profile dev-ops type jobs like lints, builds, formatters and
    so-on, so millisecond or lower fidelity isn't *required* and may add
    overhead.
    """

    label: str
    info: TimeInfo


TimedEntries = typing.List[TimeEntry]
