import io
from contextlib import redirect_stdout
from datetime import timedelta

from runem.report import report_on_run
from runem.types import JobReturn, JobRunMetadata, JobRunMetadatasByPhase, JobTiming


def test_report_on_run_basic_call() -> None:
    job_timing_1: JobTiming = ("job label 1", timedelta(seconds=0))
    job_timing_2: JobTiming = ("job label 2", timedelta(seconds=1))
    job_return: JobReturn = None  # typing.Optional[JobReturnData]
    job_run_metadata_1: JobRunMetadata = (job_timing_1, job_return)
    job_run_metadata_2: JobRunMetadata = (job_timing_2, job_return)
    job_run_metadatas: JobRunMetadatasByPhase = {
        "phase 1": [
            job_run_metadata_1,
            job_run_metadata_2,
        ]
    }
    with io.StringIO() as buf, redirect_stdout(buf):
        report_on_run(
            phase_run_oder=("phase 1",),
            job_run_metadatas=job_run_metadatas,
            overall_runtime=timedelta(0),
        )
        run_command_stdout = buf.getvalue()
    assert run_command_stdout.split("\n") == [
        "runem: reports:",
        "runem                  [0.0]",
        "├phase 1 (total)       [1.0]  ████████████████████████████████████████",
        "│├phase 1.job label 2  [1.0]  ████████████████████████████████████████",
        "",
    ]


def test_report_on_run_reports() -> None:
    job_return_1: JobReturn = {
        "reportUrls": [
            ("dummy report label", "/dummy/report/url"),
        ]
    }
    job_return_2: JobReturn = None  # typing.Optional[JobReturnData]
    job_timing_1: JobTiming = ("job label 1", timedelta(seconds=0))
    job_timing_2: JobTiming = ("job label 2", timedelta(seconds=1))
    job_run_metadata_1: JobRunMetadata = (job_timing_1, job_return_1)
    job_run_metadata_2: JobRunMetadata = (job_timing_2, job_return_2)
    job_run_metadatas: JobRunMetadatasByPhase = {
        "phase 1": [
            job_run_metadata_1,
            job_run_metadata_2,
        ]
    }
    with io.StringIO() as buf, redirect_stdout(buf):
        report_on_run(
            phase_run_oder=("phase 1",),
            job_run_metadatas=job_run_metadatas,
            overall_runtime=timedelta(0),
        )
        run_command_stdout = buf.getvalue()
    assert run_command_stdout.split("\n") == [
        "runem: reports:",
        "runem                  [0.0]",
        "├phase 1 (total)       [1.0]  ████████████████████████████████████████",
        "│├phase 1.job label 2  [1.0]  ████████████████████████████████████████",
        "runem: report: dummy report label: /dummy/report/url",
        "",
    ]
