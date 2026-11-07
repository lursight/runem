import io
from contextlib import redirect_stdout

from runem.report.report_on_run import _print_reports_by_phase
from runem.report.runem_metrics import JobRunReportByPhase
from runem.types.common import OrderedPhases


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
