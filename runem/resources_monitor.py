import pathlib
import typing
from multiprocessing.managers import ValueProxy
from time import sleep

from runem.log import log

try:
    from psutil import cpu_percent as get_cpu_percent
    from psutil import virtual_memory as get_virtual_memory
except ImportError:  # pragma: FIXME: add code coverage
    get_cpu_percent = None  # type: ignore[assignment]
    get_virtual_memory = None  # type: ignore[assignment]

# we get the values as str, and don't, for now, convert to int
CpuUsagePercent = str
MemoryUsagePercent = str

Sample = typing.Tuple[CpuUsagePercent, MemoryUsagePercent]
SamplesFile = pathlib.Path(".runem.samples")


def _get_sample() -> Sample:
    """Returns a single sample data."""
    assert get_cpu_percent is not None
    assert get_virtual_memory is not None
    cpu_percent: float = get_cpu_percent(interval=1)
    memory_percent: float = get_virtual_memory().percent

    # print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_usage}MB")
    return f"{cpu_percent}", f"{memory_percent}"


def monitor_resources(
    sample_frequency: float,
    running_jobs: typing.Dict[str, str],  # DictProxy[typing.Any, typing.Any],
    is_running: ValueProxy[bool],
    verbose: bool,
) -> None:
    """At `sample_frequency` takes computer resource samples and writes them to disk."""
    if get_cpu_percent is None:
        raise RuntimeError(
            (
                "psutil is not installed, please call `pip install psutil` and "
                "re-run runem"
            )
        )

    sample_doc: pathlib.Path = SamplesFile
    if not sample_doc.exists():
        sample_doc.write_text("job name, cpu%, mem MB")
    with sample_doc.open(mode="a") as sample_file:
        while is_running:
            number_running: int = len(running_jobs.keys())
            if number_running == 0:
                if verbose:
                    log("waiting for jobs to start")
            else:
                assert number_running == 1, (
                    "more than one process running in resource-monitor mode, "
                    "results will be tainted"
                )

                # as asserted above this is a highlander variable, there can be only one.
                running_job_uuid: str = list(running_jobs.keys())[0]

                job_name: str = running_jobs[running_job_uuid]
                sample: Sample = _get_sample()
                sample_file.write(f"{job_name},{','.join(sample)}\n")

            sleep(sample_frequency)
