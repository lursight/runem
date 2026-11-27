from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.timed_job_context import timed_job_context
from runem.report.metrics.timing_info import TimeInfo


def test_timed_job_context_records_job_and_sub_command_timings() -> None:
    command_time = TimeInfo(start=1, end=3)

    with timed_job_context("build") as timing_context:
        timing_context.record_sub_job_time_cb("compile", command_time)

    assert timing_context.future.done()
    job_timing = timing_context.future.result()
    assert isinstance(job_timing, JobTiming)
    assert job_timing.job.label == "build"
    assert job_timing.job.info.end >= job_timing.job.info.start
    assert job_timing.job.info.dur >= timedelta(0)
    assert len(job_timing.commands) == 1
    assert job_timing.commands[0].label == "compile"
    assert job_timing.commands[0].info == command_time


def test_timed_job_context_resolves_timing_when_body_raises() -> None:
    with pytest.raises(RuntimeError, match="job failed"):
        with timed_job_context("build") as timing_context:
            raise RuntimeError("job failed")

    assert timing_context.future.done()
    job_timing = timing_context.future.result()
    assert job_timing.job.label == "build"
    assert job_timing.commands == []


def test_timed_job_context_handles_timing_context_entry_failure() -> None:
    timing_context_manager = MagicMock()
    timing_context_manager.__enter__.side_effect = RuntimeError("clock failed")

    with patch(
        "runem.report.metrics.timed_job_context.timed_context",
        return_value=timing_context_manager,
    ):
        timed_context = timed_job_context("build")
        with pytest.raises(RuntimeError, match="clock failed"):
            timed_context.__enter__()
