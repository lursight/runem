import io
import typing
from contextlib import redirect_stdout
from datetime import timedelta

from runem.job.job_return import JobReturn
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.report_on_run import report_on_run
from runem.report.runem_metrics import JobRunMetadata, JobRunMetadatasByPhase
from tests.utils.sanitise_reports_footer import sanitise_reports_footer


def test_sanitise_reports_footer_removes_all_bar_chars_2() -> None:
    """Tries to test that we handle all bar-graph characters.

    This ensures we know that we are sanitising the report data nicely.
    """
    phase_run_order: typing.List[str] = []
    job_run_metadatas: JobRunMetadatasByPhase = {}
    for multiplier in [1]:  # ,2,3,4,5,6,7,8,9,10]:
        fractional_times: typing.List[JobRunMetadata] = []
        for seconds in range(15):  # 1 + 2 +3.. +14 = 105 near enough to 100%
            seconds = seconds * multiplier
            job_timing: JobTiming = {
                "job": (f"job {seconds}", timedelta(seconds=seconds)),
                "commands": [],
            }
            job_return: JobReturn = None  # typing.Optional[JobReturnData]
            job_run_metadata: JobRunMetadata = (job_timing, job_return)
            fractional_times.append(job_run_metadata)
        phase_name: str = f"phase {multiplier}"
        phase_run_order.append(phase_name)
        job_run_metadatas[phase_name] = fractional_times

    with io.StringIO() as buf, redirect_stdout(buf):
        system_time_spent: timedelta
        wall_clock_time_saved: timedelta
        system_time_spent, wall_clock_time_saved = report_on_run(
            phase_run_oder=tuple(phase_run_order),
            job_run_metadatas=job_run_metadatas,
            wall_clock_for_runem_main=timedelta(
                # mimic a value that is slightly larger than the largest single
                # job in the single phase.
                seconds=15
            ),
        )
        run_command_stdout = sanitise_reports_footer(buf.getvalue())
    assert run_command_stdout == [
        "runem: reports:",
        "runem (total wall-clock)  [ <float>]",
        " └phase 1 (user-time)     [<float>]",
        "  ├job 1                  [  <float>]",
        "  ├job 2                  [  <float>]",
        "  ├job 3                  [  <float>]",
        "  ├job 4                  [  <float>]",
        "  ├job 5                  [  <float>]",
        "  ├job 6                  [  <float>]",
        "  ├job 7                  [  <float>]",
        "  ├job 8                  [  <float>]",
        "  ├job 9                  [  <float>]",
        "  ├job 10                 [ <float>]",
        "  ├job 11                 [ <float>]",
        "  ├job 12                 [ <float>]",
        "  ├job 13                 [ <float>]",
        "  └job 14                 [ <float>]",
        "",
    ]
    # this floating-point comparison should be problematic but its' working for
    # now... for now.
    assert wall_clock_time_saved.total_seconds() == 90.0
    assert system_time_spent.total_seconds() == 105.0
