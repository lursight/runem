import re
import typing
from collections import defaultdict
from datetime import timedelta

from runem.log import log
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
    TimingEntries,
)

try:
    import termplotlib
except ImportError:  # pragma: FIXME: add code coverage
    termplotlib = None


def _align_bar_graphs_workaround(original_text: str) -> None:
    """Module termplotlib doesn't align floats, this fixes that.

    This makes it so we can align the point in the floating point string, without it,
    larger numbers push their bars right, instead of at the same place.
    """
    # Find the maximum width between '[' and '.' characters
    max_width = max(
        int(match.end() - match.start() - 2)
        for match in re.finditer(r"\[.*?(\d+)\.", original_text)
    )

    # Replace each line with aligned numbers
    formatted_text = re.sub(
        r"\[.*?(\d+)\.", lambda m: f"[{m.group(1):>{max_width}}.", original_text
    )

    print(formatted_text)


def _plot_times(
    overall_run_time: timedelta,
    phase_run_oder: OrderedPhases,
    timing_data: JobRunTimesByPhase,
) -> timedelta:
    """Prints a report to terminal on how well we performed.

    Also calculates the wall-clock time-saved for the user.
    """
    labels: typing.List[str] = []
    times: typing.List[float] = []
    job_time_sum: timedelta = timedelta()  # init to 0
    for idx, phase in enumerate(phase_run_oder):
        not_last_phase: bool = idx < len(phase_run_oder) - 1
        utf8_phase = "├" if not_last_phase else "└"
        utf8_phase_group = "│" if not_last_phase else " "
        # log(f"Phase '{phase}' jobs took:")
        phase_start_idx = len(labels)

        phase_job_times: timedelta = _gen_jobs_report(
            phase,
            labels,
            times,
            utf8_phase_group,
            timing_data[phase],
        )
        labels.insert(phase_start_idx, f"{utf8_phase}{phase} (total)")
        times.insert(phase_start_idx, phase_job_times.total_seconds())
        job_time_sum += phase_job_times

    runem_app_timing: typing.List[JobTiming] = timing_data["_app"]
    job_metadata: JobTiming
    for job_metadata in reversed(runem_app_timing):
        job_label, job_time_total = job_metadata["job"]
        labels.insert(0, f"├runem.{job_label}")
        times.insert(0, job_time_total.total_seconds())
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
        # ensure the graphs get aligned nicely.
        _align_bar_graphs_workaround(fig.get_string())
    else:  # pragma: FIXME: add code coverage
        for job_label, time in zip(labels, times):
            log(f"{job_label}: {time}s")

    time_saved: timedelta = job_time_sum - overall_run_time
    return time_saved


def _gen_jobs_report(
    phase: PhaseName,
    labels: typing.List[str],
    times: typing.List[float],
    utf8_phase_group: str,
    job_timings: typing.List[JobTiming],
) -> timedelta:
    """Gathers the reports for sub-jobs.

    Split out from _plot_times as the code was getting complex
    """
    job_timing: JobTiming

    # Filter out JobTiming instances with non-zero total_seconds
    non_zero_timing_data: typing.List[JobTiming] = [
        job_timing
        for job_timing in job_timings
        if job_timing["job"][1].total_seconds() != 0
    ]

    job_time_sum: timedelta = timedelta()  # init to 0
    for idx, job_timing in enumerate(non_zero_timing_data):
        not_last: bool = idx < len(non_zero_timing_data) - 1
        utf8_job = "├" if not_last else "└"
        utf8_sub_jobs = "│" if not_last else " "
        job_label, job_time_total = job_timing["job"]
        labels.append(f"{utf8_phase_group}{utf8_job}{phase}.{job_label}")
        times.append(job_time_total.total_seconds())
        job_time_sum += job_time_total
        sub_command_times: TimingEntries = job_timing["commands"]

        if len(sub_command_times) <= 1:
            # we only have one or fewer sub-commands, just show the job-time
            continue

        # also print the sub-components of the job as we have more than one
        for idx, (sub_job_label, sub_job_time) in enumerate(sub_command_times):
            sub_utf8 = "├"
            if idx == len(sub_command_times) - 1:
                sub_utf8 = "└"
            labels.append(
                f"{utf8_phase_group}{utf8_sub_jobs}{sub_utf8}{phase}.{job_label}.{sub_job_label}"
            )
            times.append(sub_job_time.total_seconds())
    return job_time_sum


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
            log(f"report: {str(job_report_url_info[0])}: {str(job_report_url_info[1])}")


def report_on_run(
    phase_run_oder: OrderedPhases,
    job_run_metadatas: JobRunMetadatasByPhase,
    overall_runtime: timedelta,
) -> timedelta:
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
    # Also, calculate the time saved by runem, a key selling-point metric
    time_saved: timedelta = _plot_times(
        overall_run_time=overall_runtime,
        phase_run_oder=phase_run_oder,
        timing_data=timing_data,
    )

    # Penultimate-ly print out the available reports grouped by run-phase.
    _print_reports_by_phase(phase_run_oder, report_data)

    # Return the key metric for runem, the wall-clock time saved to the user
    # TODO: write this to disk
    return time_saved
