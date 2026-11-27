"""Generic Timing Information.

Records *only* time info like:
    - start
    - end
    - duration
    - possibly timezone
    - etc.

`TimeInfo` is **NOT** `TimeEntry` because:
    - TimeInfo is meta-data agnostic
    - TimedEntry is designed:
      > .. to be a labeled, context-aware entry.
      > .. to be used for:
          - visualisations
          - analysis
          - other data-lookups.
"""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class TimeInfo:
    start: float
    end: float

    @property
    def dur(self) -> timedelta:
        """Return the elapsed time represented by this interval."""
        return timedelta(seconds=self.end - self.start)
