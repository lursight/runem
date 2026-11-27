import typing
from collections import defaultdict
from datetime import timedelta

from runem.job.job_return import JobReturn
from runem.log import log
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.report_url import ReportUrlInfo, ReportUrls
from runem.report.runem_metrics import (
    JobRunMetadatasByPhase,
    JobRunReportByPhase,
    JobRunTimesByPhase,
)
from runem.report.visualisations.run_bars import (
    plot_run_bars,
)
from runem.types.common import OrderedPhases, PhaseName


def _print_reports_by_phase(
    phase_run_oder: OrderedPhases, report_data: JobRunReportByPhase
) -> None:
    """Logs out the reports by grouped by phase."""
    for phase in phase_run_oder:
        report_urls: ReportUrls = report_data[phase]
        job_report_url_info: ReportUrlInfo
        for job_report_url_info in report_urls:
            if not job_report_url_info:
                continue
            log(
                f"report: [blue]{str(job_report_url_info[0])}[/blue]: "
                f"{str(job_report_url_info[1])}"
            )


def report_on_run(
    phase_run_oder: OrderedPhases,
    job_run_metadatas: JobRunMetadatasByPhase,
    wall_clock_for_runem_main: timedelta,
) -> typing.Tuple[timedelta, timedelta]:
    """Generate high-level reports AND prints out any reports returned by jobs.

    IMPORTANT: returns the wall-clock time saved to the user.
    """
    log("reports:")

    # First, collate all data, timing and reports
    timing_data: JobRunTimesByPhase = defaultdict(list)
    report_data: JobRunReportByPhase = defaultdict(list)
    phase: PhaseName
    for phase in job_run_metadatas:
        timing: JobTiming
        reports: JobReturn
        for timing, reports in job_run_metadatas[phase]:
            timing_data[phase].append(timing)
            if reports:
                # the job returned some report urls, record them against the
                # job's phase
                report_data[phase].extend(reports["reportUrls"])

    # Now plot the times on the terminal to give a visual report of the timing.
    time_metrics: typing.Tuple[timedelta, timedelta] = plot_run_bars(
        wall_clock_for_runem_main=wall_clock_for_runem_main,
        phase_run_order=phase_run_oder,
        timing_data=timing_data,
    )

    # Penultimate-ly print out the available reports grouped by run-phase.
    _print_reports_by_phase(phase_run_oder, report_data)

    # Return the key metrics for runem, the system vs wall-clock time saved to
    # the user
    # TODO: write this to disk
    return time_metrics
