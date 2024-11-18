#!/usr/bin/env python3
"""`runem`, runs Lursight's dev-ops tools, hopefully as fast as possible.

We don't yet:
- account for load
- check for diffs in code to only test changed code
- do any git-related stuff, like:
  - compare head to merge-target branch
  - check for changed files
- support non-git repos
- not stream stdout to terminal
- have inter-job dependencies as that requires a smarter scheduler, we workaround
  this with phases, for now

We do:
- use git ls-files
- run as many jobs as possible
- hope that resources are enough i.e. we DO NOT measure resource use, yet.
- time tests and tell you what used the most time, and how much time run-tests saved
  you
"""
import multiprocessing
import os
import pathlib
import sys
import time
import typing
from collections import defaultdict
from datetime import timedelta
from itertools import repeat
from multiprocessing.managers import DictProxy, ValueProxy
from timeit import default_timer as timer
from types import TracebackType

from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.spinner import Spinner
from rich.text import Text

from runem.command_line import parse_args
from runem.config import load_project_config, load_user_configs
from runem.config_metadata import ConfigMetadata
from runem.config_parse import load_config_metadata
from runem.files import find_files
from runem.job_execute import job_execute
from runem.job_filter import filter_jobs
from runem.log import error, log, warn
from runem.report import report_on_run
from runem.types.common import OrderedPhases, PhaseName
from runem.types.filters import FilePathListLookup
from runem.types.hooks import HookName
from runem.types.runem_config import Config, Jobs, PhaseGroupedJobs
from runem.types.types_jobs import (
    JobReturn,
    JobRunMetadata,
    JobRunMetadatasByPhase,
    JobTiming,
)
from runem.utils import printable_set

rich_console = Console()


def _determine_run_parameters(argv: typing.List[str]) -> ConfigMetadata:
    """Loads config, parsing cli input and produces the run config.

    This is where the power of run'em resides. We match a declarative config with useful
    command-line switches to make choosing which jobs to run fast and intuitive.

    Return a ConfigMetadata object with all the required information.
    """
    config: Config
    cfg_filepath: pathlib.Path
    config, cfg_filepath = load_project_config()
    user_configs: typing.List[typing.Tuple[Config, pathlib.Path]] = load_user_configs()
    config_metadata: ConfigMetadata = load_config_metadata(
        config, cfg_filepath, user_configs, verbose=("--verbose" in argv)
    )

    # Now we parse the cli arguments extending them with information from the
    # .runem.yml config.
    config_metadata = parse_args(config_metadata, argv)

    if config_metadata.args.verbose:
        log(f"loaded config from {cfg_filepath}")

    return config_metadata


class DummySpinner(ConsoleRenderable):  # pragma: no cover
    """A dummy spinner for when spinners are disabled."""

    def __init__(self) -> None:
        self.text = ""

    def __rich__(self) -> Text:
        """Return a rich Text object for rendering."""
        return Text(self.text)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Yield an empty string or placeholder text."""
        yield Text(self.text)

    def __enter__(self) -> None:
        """Support for context manager."""
        pass

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[TracebackType],
    ) -> None:
        """Support for context manager."""
        pass


def _update_progress(
    label: str,
    running_jobs: typing.Dict[str, str],
    completed_jobs: typing.Dict[str, str],
    all_jobs: Jobs,
    is_running: ValueProxy[bool],
    num_workers: int,
    show_spinner: bool,
) -> None:
    """Updates progress report periodically for running tasks.

    Args:
        label (str): The identifier.
        running_jobs (Dict[str, str]): The currently running jobs.
        all_jobs (Jobs): All jobs, encompassing both completed and running jobs.
        is_running (ValueProxy[bool]): Flag indicating if jobs are still running.
        num_workers (int): Indicates the number of workers performing the jobs.
    """
    # Using the `rich` module to show a loading spinner on console
    spinner: typing.Union[Spinner, DummySpinner]
    if show_spinner:
        spinner = Spinner("dots", text="Starting tasks...")
    else:
        spinner = DummySpinner()

    last_running_jobs_set: typing.Set[str] = set()

    with rich_console.status(spinner):
        while is_running.value:
            running_jobs_set: typing.Set[str] = set(running_jobs.values())

            # Progress report
            progress: str = f"{len(completed_jobs)}/{len(all_jobs)}"
            running_jobs_list = printable_set(
                running_jobs_set
            )  # Reflect current running jobs accurately
            report: str = f"{label}: {progress}({num_workers}): {running_jobs_list}"
            if show_spinner:
                spinner.text = report
            else:
                if last_running_jobs_set != running_jobs_set:
                    rich_console.log(report)

            # Sleep for reduced CPU usage
            time.sleep(0.1)


def _process_jobs(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
    phase: PhaseName,
    jobs: Jobs,
    show_spinner: bool,
) -> typing.Optional[BaseException]:
    """Execute each given job asynchronously.

    This is where the major real-world time savings happen, and it could be
    better, much, much better.

    TODO: this is where we do the scheduling, if we wanted to be smarter about
          it and, for instance, run the longest-running job first with quicker
          jobs completing around it, then we would work out that schedule here.

    returns the exception if the any of sub-procs fails, None otherwise
    """
    max_num_concurrent_procs: int = (
        config_metadata.args.procs
        if config_metadata.args.procs != -1
        else multiprocessing.cpu_count()
    )
    num_concurrent_procs: int = min(max_num_concurrent_procs, len(jobs))
    log(
        (
            f"Running '{phase}' with {num_concurrent_procs} workers (of "
            f"{max_num_concurrent_procs} max) processing {len(jobs)} jobs"
        )
    )

    subprocess_error: typing.Optional[BaseException] = None

    with multiprocessing.Manager() as manager:
        running_jobs: DictProxy[typing.Any, typing.Any] = manager.dict()
        completed_jobs: DictProxy[typing.Any, typing.Any] = manager.dict()
        is_running: ValueProxy[bool] = manager.Value("b", True)

        terminal_writer_process = multiprocessing.Process(
            target=_update_progress,
            args=(
                phase,
                running_jobs,
                completed_jobs,
                jobs,
                is_running,
                num_concurrent_procs,
                show_spinner,
            ),
        )
        terminal_writer_process.start()

        try:
            with multiprocessing.Pool(processes=num_concurrent_procs) as pool:
                # use starmap so we can pass down the job-configs and the args and the files
                in_out_job_run_metadatas[phase] = pool.starmap(
                    job_execute,  # no kwargs passed for jobs here
                    zip(
                        jobs,
                        repeat(running_jobs),
                        repeat(completed_jobs),
                        repeat(config_metadata),
                        repeat(file_lists),
                    ),
                )
        except BaseException as err:  # pylint: disable=broad-exception-caught
            subprocess_error = err
        finally:
            # Signal the terminal_writer process to exit
            is_running.value = False
            terminal_writer_process.join()

    return subprocess_error


def _process_jobs_by_phase(
    config_metadata: ConfigMetadata,
    file_lists: FilePathListLookup,
    filtered_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_run_metadatas: JobRunMetadatasByPhase,
    show_spinner: bool,
) -> typing.Optional[BaseException]:
    """Execute each job asynchronously, grouped by phase.

    Whilst it is conceptually useful to group jobs by 'phase', Phases are
    ostensibly a poor-man's dependency graph. With a proper dependency graph
    Phases could be phased out, or at least used less. For new users, and to get
    a quick and dirty solution up and running, Phases are probably a very good
    idea and easy to grasp.

    TODO: augment (NOT REPLACE) with dependency graph. New users and hacker
          dev-ops/SREs find phases useful and, more importantly, quick to
          implement.

    returns the exception, if any thrown during run.
    """
    for phase in config_metadata.phases:
        jobs = filtered_jobs_by_phase[phase]
        if not jobs:
            # As previously reported, no jobs for this phase
            continue

        if config_metadata.args.verbose:
            log(f"Running Phase {phase}")

        failure_exception: typing.Optional[BaseException] = _process_jobs(
            config_metadata,
            file_lists,
            in_out_job_run_metadatas,
            phase,
            jobs,
            show_spinner,
        )
        if failure_exception is not None:
            if config_metadata.args.verbose:
                error(f"running phase {phase}: aborting run")
            return failure_exception

    # ALl phases completed aok.
    return None


MainReturnType = typing.Tuple[
    ConfigMetadata, JobRunMetadatasByPhase, typing.Optional[BaseException]
]


def _main(
    argv: typing.List[str],
) -> MainReturnType:
    start = timer()

    config_metadata: ConfigMetadata = _determine_run_parameters(argv)

    # first anchor the cwd to the config-file, so that git ls-files works
    os.chdir(config_metadata.cfg_filepath.parent)

    file_lists: FilePathListLookup = find_files(config_metadata)
    if not file_lists:
        warn("no files found")
        return (config_metadata, {}, None)

    if config_metadata.args.verbose:
        log(f"found {len(file_lists)} batches, ", end="")
        for tag in sorted(file_lists.keys()):
            file_list = file_lists[tag]
            log(f"{len(file_list)} '{tag}' files, ", decorate=False, end="")
        log(decorate=False)  # new line

    filtered_jobs_by_phase: PhaseGroupedJobs = filter_jobs(
        config_metadata=config_metadata,
    )
    end = timer()

    job_run_metadatas: JobRunMetadatasByPhase = defaultdict(list)
    pre_build_time: JobTiming = {
        "job": ("pre-build", (timedelta(seconds=end - start))),
        "commands": [],
    }
    job_run_metadatas["_app"].append((pre_build_time, None))

    start = timer()

    failure_exception: typing.Optional[BaseException] = _process_jobs_by_phase(
        config_metadata,
        file_lists,
        filtered_jobs_by_phase,
        job_run_metadatas,
        show_spinner=config_metadata.args.show_spinner,
    )

    end = timer()

    phase_run_timing: JobTiming = {
        "job": ("run-phases", timedelta(seconds=end - start)),
        "commands": [],
    }
    phase_run_report: JobReturn = None
    phase_run_metadata: JobRunMetadata = (phase_run_timing, phase_run_report)
    job_run_metadatas["_app"].append(phase_run_metadata)
    return config_metadata, job_run_metadatas, failure_exception


def timed_main(argv: typing.List[str]) -> None:
    """A main-entry point that runs the application reports on it.

    IMPORTANT: this should remain a lightweight wrapper around _main() so that timings
               are representative.
    """
    start = timer()
    config_metadata: ConfigMetadata
    job_run_metadatas: JobRunMetadatasByPhase
    failure_exception: typing.Optional[BaseException]
    config_metadata, job_run_metadatas, failure_exception = _main(argv)
    phase_run_oder: OrderedPhases = config_metadata.phases
    end = timer()
    time_taken: timedelta = timedelta(seconds=end - start)
    wall_clock_time_saved: timedelta
    system_time_spent: timedelta
    system_time_spent, wall_clock_time_saved = report_on_run(
        phase_run_oder, job_run_metadatas, time_taken
    )
    message: str = "DONE: runem took"
    if failure_exception:
        message = "FAILED: your jobs failed after"
    log(
        (
            f"{message}: {time_taken.total_seconds()}s, "
            f"saving you {wall_clock_time_saved.total_seconds()}s, "
            f"without runem you would have waited {system_time_spent.total_seconds()}s"
        )
    )

    config_metadata.hook_manager.invoke_hooks(
        hook_name=HookName.ON_EXIT,
        config_metadata=config_metadata,
        wall_clock_time_saved=wall_clock_time_saved,
    )

    if failure_exception is not None:
        # we got a failure somewhere, now that we've reported the timings we
        # re-raise.
        raise failure_exception


if __name__ == "__main__":
    timed_main(sys.argv)
