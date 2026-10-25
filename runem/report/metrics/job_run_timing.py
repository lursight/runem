import typing

from runem.report.metrics.timing import TimingEntries, TimingEntry


class JobTiming(typing.TypedDict, total=True):
    """A hierarchy of timing info. Job->JobCommands.

    The overall time for a job is in 'job', the child calls to run_command are in
    'commands'
    """

    job: TimingEntry  # the overall time for a job
    commands: TimingEntries  # timing for each call to `run_command`
