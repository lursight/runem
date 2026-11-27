"""Terminal bar graph for run timing data."""

import re
import typing
from datetime import timedelta

from runem.log import log
from runem.report.metrics.job_run_timing import JobTiming
from runem.report.metrics.time_entry import TimedEntries
from runem.report.runem_metrics import JobRunTimesByPhase
from runem.types.common import OrderedPhases, PhaseName

try:
    import termplotlib
except ImportError:  # pragma: FIXME: add code coverage
    termplotlib = None


def _align_bar_graphs_workaround(original_text: str) -> str:
    """Align floating point values so bar starts share the same column."""
    max_width = max(
        int(match.end() - match.start() - 2)
        for match in re.finditer(r"\[.*?(\d+)\.", original_text)
    )
    return re.sub(
        r"\[.*?(\d+)\.", lambda match: f"[{match.group(1):>{max_width}}.", original_text
    )


def replace_bar_graph_characters(text: str, end_str: str, replace_char: str) -> str:
    """Replace bar glyphs on lines that contain ``end_str``."""
    block_chars = "▏▎▍▋▊▉█▌▐▄▀─░·"
    text_lines = text.split("\n")
    modified_lines = [
        line.translate(str.maketrans(block_chars, replace_char * len(block_chars)))
        if end_str in line
        else line
        for line in text_lines
    ]
    return "\n".join(modified_lines)


def _semi_shade_phase_totals(text: str) -> str:
    return replace_bar_graph_characters(text, "(user-time)", "░")


def _dot_jobs(text: str) -> str:
    return replace_bar_graph_characters(text, "(+)", "·")


def plot_run_bars(
    wall_clock_for_runem_main: timedelta,
    phase_run_order: OrderedPhases,
    timing_data: JobRunTimesByPhase,
) -> typing.Tuple[timedelta, timedelta]:
    """Print timing bars and return total work time and time saved."""
    labels: typing.List[str] = []
    times: typing.List[float] = []
    system_time_spent = timedelta()

    for index, phase in enumerate(phase_run_order):
        phase_is_not_last = index < len(phase_run_order) - 1
        phase_branch = " ├" if phase_is_not_last else " └"
        phase_prefix = " │" if phase_is_not_last else "  "
        phase_start_index = len(labels)
        phase_job_time = _gen_jobs_report(
            phase, labels, times, phase_prefix, timing_data[phase]
        )
        labels.insert(phase_start_index, f"{phase_branch}{phase} (user-time)")
        times.insert(phase_start_index, phase_job_time.total_seconds())
        system_time_spent += phase_job_time

    app_timings: typing.List[JobTiming] = timing_data["_app"]
    for index, job_timing in enumerate(reversed(app_timings)):
        group_branch = "├" if index > 0 else "└"
        labels.insert(0, f"{group_branch}runem.{job_timing.job.label}")
        times.insert(0, job_timing.job.info.dur.total_seconds())
    labels.insert(0, "runem (total wall-clock)")
    times.insert(0, wall_clock_for_runem_main.total_seconds())

    if termplotlib:
        figure = termplotlib.figure()
        figure.barh(times, labels, force_ascii=False)
        shaded_bars = _semi_shade_phase_totals(figure.get_string())
        dotted_bars = _dot_jobs(shaded_bars)
        print(_align_bar_graphs_workaround(dotted_bars))
    else:  # pragma: FIXME: add code coverage
        for job_label, duration in zip(labels, times):
            log(f"{job_label}: {duration}s")

    wall_clock_time_saved = system_time_spent - wall_clock_for_runem_main
    return system_time_spent, wall_clock_time_saved


def _gen_jobs_report(
    phase: PhaseName,
    labels: typing.List[str],
    times: typing.List[float],
    phase_prefix: str,
    job_timings: typing.List[JobTiming],
) -> timedelta:
    """Append one phase's jobs and commands; return the jobs' total duration."""
    non_zero_timings = [
        timing for timing in job_timings if timing.job.info.dur.total_seconds() != 0
    ]
    job_time_sum = timedelta()
    for index, job_timing in enumerate(non_zero_timings):
        job_is_not_last = index < len(non_zero_timings) - 1
        job_branch = "├" if job_is_not_last else "└"
        command_prefix = "│" if job_is_not_last else " "
        labels.append(f"{phase_prefix}{job_branch}{job_timing.job.label}")
        job_duration = job_timing.job.info.dur
        times.append(job_duration.total_seconds())
        job_time_sum += job_duration

        command_timings: TimedEntries = job_timing.commands
        if len(command_timings) <= 1:
            continue
        for command_index, command_timing in enumerate(command_timings):
            command_branch = "├" if command_index < len(command_timings) - 1 else "└"
            labels.append(
                f"{phase_prefix}{command_prefix}{command_branch}"
                f"{command_timing.label} (+)"
            )
            times.append(command_timing.info.dur.total_seconds())
    return job_time_sum
