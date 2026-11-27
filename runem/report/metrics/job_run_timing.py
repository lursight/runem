from dataclasses import dataclass

from runem.report.metrics.time_entry import TimedEntries, TimeEntry


@dataclass(frozen=True)
class JobTiming:
    """A hierarchy of timing info. Job->JobCommands.

    The overall time for a job is in 'job', the child calls to run_command are in
    'commands'
    """

    job: TimeEntry  # the overall time for a job
    commands: TimedEntries  # timing for each call to `run_command`
