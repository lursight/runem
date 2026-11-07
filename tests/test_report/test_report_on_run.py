import io
from contextlib import redirect_stdout
from datetime import timedelta

from runem.job.job_return import JobReturn
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.report_on_run import report_on_run
from runem.report.runem_metrics import JobRunMetadata, JobRunMetadatasByPhase


def test_report_on_run_basic_call() -> None:
    job_timing_1: JobTiming = {"job": ("job 1", timedelta(seconds=0)), "commands": []}
    job_timing_2: JobTiming = {
        "job": (
            "job label 2",
            timedelta(seconds=1000, milliseconds=1, microseconds=1),
        ),
        "commands": [
            ("sub1", timedelta(seconds=500)),
            ("sub2", timedelta(seconds=500)),
        ],
    }
    job_timing_3: JobTiming = {
        "job": (
            "another job 3",
            timedelta(seconds=2),
        ),
        "commands": [],
    }
    job_timing_4: JobTiming = {
        "job": (
            "another job 4",
            timedelta(seconds=250),
        ),
        "commands": [],
    }
    job_return: JobReturn = None  # typing.Optional[JobReturnData]
    job_run_metadata_1: JobRunMetadata = (job_timing_1, job_return)
    job_run_metadata_2: JobRunMetadata = (job_timing_2, job_return)
    job_run_metadata_3: JobRunMetadata = (job_timing_3, job_return)
    job_run_metadata_4: JobRunMetadata = (job_timing_4, job_return)
    job_run_metadatas: JobRunMetadatasByPhase = {
        "phase 1": [
            job_run_metadata_1,
            job_run_metadata_2,
            job_run_metadata_3,
            job_run_metadata_4,
        ]
    }
    with io.StringIO() as buf, redirect_stdout(buf):
        system_time_spent: timedelta
        wall_clock_time_saved: timedelta
        system_time_spent, wall_clock_time_saved = report_on_run(
            phase_run_oder=("phase 1",),
            job_run_metadatas=job_run_metadatas,
            wall_clock_for_runem_main=timedelta(
                # mimic a value that is slightly larger than the largest single
                # job in the single phase.
                seconds=1000.5
            ),
        )
        run_command_stdout = buf.getvalue()
    assert run_command_stdout.split("\n") == [
        "runem: reports:",
        "runem (total wall-clock)  [1000.500000]  ████████████████████████████████",
        (
            " └phase 1 (user-time)     [1252.001001]  "
            "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
        ),
        "  ├job label 2            [1000.001001]  ████████████████████████████████",
        "  │├sub1 (+)              [ 500.000000]  ················",
        "  │└sub2 (+)              [ 500.000000]  ················",
        "  ├another job 3          [   2.000000]  ▏",
        "  └another job 4          [ 250.000000]  ████████",
        "",
    ]
    # this floating-point comparison should be problematic but its' working for
    # now... for now.
    assert wall_clock_time_saved.total_seconds() == 251.501001
    assert system_time_spent.total_seconds() == 1252.001001


def test_report_on_run_reports() -> None:
    job_return_1: JobReturn = {
        "reportUrls": [
            ("dummy report label", "/dummy/report/url"),
        ]
    }
    job_return_2: JobReturn = None  # typing.Optional[JobReturnData]
    job_timing_1: JobTiming = {
        "job": ("job label 1", timedelta(seconds=0)),
        "commands": [],
    }
    job_timing_2: JobTiming = {
        "job": (
            "job label 2",
            timedelta(seconds=1000, milliseconds=1, microseconds=1),
        ),
        "commands": [],
    }
    job_timing_3: JobTiming = {
        "job": (
            "another job 3",
            timedelta(seconds=2),
        ),
        "commands": [],
    }
    job_run_metadata_1: JobRunMetadata = (job_timing_1, job_return_1)
    job_run_metadata_2: JobRunMetadata = (job_timing_2, job_return_2)
    job_run_metadata_3: JobRunMetadata = (job_timing_3, job_return_2)
    job_run_metadatas: JobRunMetadatasByPhase = {
        "phase 1": [
            job_run_metadata_1,
            job_run_metadata_2,
            job_run_metadata_3,
        ]
    }
    with io.StringIO() as buf, redirect_stdout(buf):
        report_on_run(
            phase_run_oder=("phase 1",),
            job_run_metadatas=job_run_metadatas,
            wall_clock_for_runem_main=timedelta(0),
        )
        run_command_stdout = buf.getvalue()
    assert run_command_stdout.split("\n") == [
        "runem: reports:",
        "runem (total wall-clock)  [   0.000000]",
        (
            " └phase 1 (user-time)     [1002.001001]  "
            "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
        ),
        (
            "  ├job label 2            [1000.001001]  "
            "███████████████████████████████████████▉"
        ),
        "  └another job 3          [   2.000000]  ▏",
        "runem: report: dummy report label: /dummy/report/url",
        "",
    ]
