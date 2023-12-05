import typing
from collections import defaultdict
from datetime import timedelta

from runem.types import (
    JobReturn,
    JobRunMetadatasByPhase,
    JobRunReportByPhase,
    JobRunTimesByPhase,
    JobTiming,
    OrderedPhases,
    PhaseName,
    ReportUrlInfo,
    ReportUrls,
)

try:
    import termplotlib
except ImportError:  # pragma: FIXME: add code coverage
    termplotlib = None


def _plot_times(
    overall_run_time: timedelta,
    phase_run_oder: OrderedPhases,
    timing_data: JobRunTimesByPhase,
) -> timedelta:
    """Prints a report to terminal on how well we performed."""
    labels: typing.List[str] = []
    times: typing.List[float] = []
    job_time_sum: timedelta = timedelta()  # init to 0
    for phase in phase_run_oder:
        # print(f"Phase '{phase}' jobs took:")
        phase_total_time: float = 0.0
        phase_start_idx = len(labels)
        for label, job_time in timing_data[phase]:
            if job_time.total_seconds() == 0:
                continue
            labels.append(f"│├{phase}.{label}")
            times.append(job_time.total_seconds())
            job_time_sum += job_time
            phase_total_time += job_time.total_seconds()
        labels.insert(phase_start_idx, f"├{phase} (total)")
        times.insert(phase_start_idx, phase_total_time)

    for label, job_time in reversed(timing_data["_app"]):
        labels.insert(0, f"├runem.{label}")
        times.insert(0, job_time.total_seconds())
    labels.insert(0, "runem")
    times.insert(0, overall_run_time.total_seconds())
    if termplotlib:
        fig = termplotlib.figure()
        # cspell:disable-next-line
        fig.barh(
            times,
            labels,
            force_ascii=False,
        )
        fig.show()
    else:  # pragma: FIXME: add code coverage
        for label, time in zip(labels, times):
            print(f"{label}: {time}s")

    time_saved: timedelta = job_time_sum - overall_run_time
    return time_saved


def report_on_run(
    phase_run_oder: OrderedPhases,
    job_run_metadatas: JobRunMetadatasByPhase,
    overall_runtime: timedelta,
):
    print("runem: reports:")
    timing_data: JobRunTimesByPhase = defaultdict(list)
    report_data: JobRunReportByPhase = defaultdict(list)
    phase: PhaseName
    for phase in job_run_metadatas:
        timing: JobTiming
        reports: JobReturn
        for timing, reports in job_run_metadatas[phase]:
            timing_data[phase].append(timing)
            if reports:
                report_data[phase].extend(reports["reportUrls"])
    time_saved: timedelta = _plot_times(
        overall_run_time=overall_runtime,
        phase_run_oder=phase_run_oder,
        timing_data=timing_data,
    )
    for phase in phase_run_oder:
        report_urls: ReportUrls = report_data[phase]
        job_report_url_info: ReportUrlInfo
        for job_report_url_info in report_urls:
            if not job_report_url_info:
                continue
            print(
                f"report: {str(job_report_url_info[0])}: {str(job_report_url_info[1])}"
            )
    return time_saved
