import io
from contextlib import redirect_stdout
from datetime import timedelta

from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.time_entry import TimeEntry
from runem.report.metrics.timing_info import TimeInfo
from runem.report.runem_metrics import JobRunTimesByPhase
from runem.report.visualisations.run_bars import plot_run_bars


def test_plot_run_bars_prints_bars_and_returns_work_metrics() -> None:
    phase_timings = [
        JobTiming(
            job=TimeEntry(
                label="job",
                info=TimeInfo(start=0, end=3),
            ),
            commands=[],
        )
    ]
    timing_data: JobRunTimesByPhase = {"build": phase_timings, "_app": []}

    with io.StringIO() as buffer, redirect_stdout(buffer):
        system_time_spent, wall_clock_time_saved = plot_run_bars(
            wall_clock_for_runem_main=timedelta(seconds=2),
            phase_run_order=("build",),
            timing_data=timing_data,
        )
        graph_output = buffer.getvalue()

    assert "build (user-time)" in graph_output
    assert "job" in graph_output
    assert system_time_spent == timedelta(seconds=3)
    assert wall_clock_time_saved == timedelta(seconds=1)
