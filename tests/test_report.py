import io
from contextlib import redirect_stdout
from datetime import timedelta

from runem.report import _print_reports_by_phase, report_on_run
from runem.types import (
    JobReturn,
    JobRunMetadata,
    JobRunMetadatasByPhase,
    JobRunReportByPhase,
    JobTiming,
    OrderedPhases,
)


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
        "runem (total wall-clock)         [1000.500000]  ████████████████████████████████",
        (
            "└phase 1 (user-time)             [1252.001001] "
            " ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
        ),
        " ├phase 1.job label 2            [1000.001001]  ████████████████████████████████",
        " │├phase 1.job label 2.sub1 (+)  [ 500.000000]  ················",
        " │└phase 1.job label 2.sub2 (+)  [ 500.000000]  ················",
        " ├phase 1.another job 3          [   2.000000]  ▏",
        " └phase 1.another job 4          [ 250.000000]  ████████",
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
        "└phase 1 (user-time)      [1002.001001]  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
        " ├phase 1.job label 2     [1000.001001]  ███████████████████████████████████████▉",
        " └phase 1.another job 3   [   2.000000]  ▏",
        "runem: report: dummy report label: /dummy/report/url",
        "",
    ]


def test_print_reports_by_phase() -> None:
    # Test data
    phase_run_order: OrderedPhases = ("phase1", "phase2", "phase3", "phase4")

    report_data: JobRunReportByPhase = {
        "ignored_phase": [
            ("no log", "not run should not appear in logs"),
        ],
        "phase1": [("report1", "path/to/report1"), ("report2", "path/to/report2")],
        "phase2": [("report3", "path/to/report3")],
        "phase3": [],  # Empty list to test handling of empty reports
        "phase4": [
            (),  # type: ignore
        ],  # Empty tuple to test handling of empty report data
    }

    # Call the function
    with io.StringIO() as buf, redirect_stdout(buf):
        _print_reports_by_phase(phase_run_order, report_data)
        run_command_stdout = buf.getvalue()

    # Assert that log is called with the expected messages
    expected_logs = [
        "runem: report: report1: path/to/report1",
        "runem: report: report2: path/to/report2",
        "runem: report: report3: path/to/report3",
        "",
    ]
    assert run_command_stdout.split("\n") == expected_logs
