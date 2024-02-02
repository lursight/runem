import copy
import pathlib
import sys
import typing
from collections import defaultdict
from collections.abc import Iterable

from runem.config_metadata import ConfigMetadata
from runem.job import Job
from runem.job_wrapper import get_job_wrapper
from runem.log import log
from runem.types import (
    Config,
    ConfigNodes,
    GlobalConfig,
    GlobalSerialisedConfig,
    JobConfig,
    JobNames,
    JobPhases,
    JobSerialisedConfig,
    JobTags,
    JobWhen,
    OptionConfigs,
    OrderedPhases,
    PhaseGroupedJobs,
    PhaseName,
    TagFileFilter,
    TagFileFilters,
    TagFileFilterSerialised,
)


def _parse_global_config(
    global_config: GlobalConfig,
) -> typing.Tuple[OrderedPhases, OptionConfigs, TagFileFilters]:
    """Parses and validates a global-config entry read in from disk.

    Returns the phases in the order we want to run them
    """
    options: OptionConfigs = ()
    if "options" in global_config and global_config["options"]:
        options = tuple(
            option_serialised["option"]
            for option_serialised in global_config["options"]
        )

    file_filters: TagFileFilters = {}
    if "files" in global_config and global_config["files"]:
        file_filter: TagFileFilterSerialised
        serialised_filters: typing.List[TagFileFilterSerialised] = global_config[
            "files"
        ]
        for file_filter in serialised_filters:
            actual_filter: TagFileFilter = file_filter["filter"]
            tag = actual_filter["tag"]
            file_filters[tag] = actual_filter

    phases: OrderedPhases = tuple()
    if "phases" in global_config:
        phases = global_config["phases"]
    return phases, options, file_filters


def _parse_job(
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    in_out_tags: JobTags,
    in_out_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_names: JobNames,
    in_out_phases: JobPhases,
    phase_order: OrderedPhases,
) -> None:
    """Parse an individual job."""
    job_name: str = Job.get_job_name(job)
    job_names_used = job_name in in_out_job_names
    if job_names_used:
        log("ERROR: duplicate job label!")
        log(f"\t'{job['label']}' is used twice or more in {str(cfg_filepath)}")
        sys.exit(1)

    # try and load the function _before_ we schedule it's execution
    get_job_wrapper(job, cfg_filepath)
    try:
        phase_id: PhaseName = job["when"]["phase"]
    except KeyError:
        fallback_phase = phase_order[0]
        log(f"WARNING: no phase found for '{job_name}', using '{fallback_phase}'")
        phase_id = fallback_phase
    in_out_jobs_by_phase[phase_id].append(job)

    in_out_job_names.add(job_name)
    in_out_phases.add(phase_id)
    job_tags: typing.Optional[JobTags] = Job.get_job_tags(job)
    if job_tags:
        in_out_tags.update(job_tags)


def parse_job_config(
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    in_out_tags: JobTags,
    in_out_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_names: JobNames,
    in_out_phases: JobPhases,
    phase_order: OrderedPhases,
) -> None:
    """Parses and validates a job-entry read in from disk.

    Returns the tags generated
    """
    try:
        # if there is more than one cwd, duplicate the job for each cwd
        generated_jobs: typing.List[JobConfig] = []
        have_ctw_cwd: bool = (("ctx" in job) and (job["ctx"] is not None)) and (
            ("cwd" in job["ctx"]) and (job["ctx"]["cwd"] is not None)
        )
        if (not have_ctw_cwd) or isinstance(
            job["ctx"]["cwd"], str  # type: ignore # handled above
        ):
            # if
            # - we don't have a cwd, ctx
            # - or if the cwd is just a string, it's a path, just use it
            generated_jobs.append(job)
        else:
            assert job["ctx"] is not None
            assert job["ctx"]["cwd"] is not None
            assert isinstance(job["ctx"]["cwd"], Iterable)
            assert isinstance(job["ctx"]["cwd"], list)
            cwd_list: typing.List[str] = job["ctx"]["cwd"]
            cwd: str
            for cwd in cwd_list:
                specialised_job_for_cwd = copy.deepcopy(job)
                # overwrite the list of cwd paths with just the single instance
                assert (
                    "ctx" in specialised_job_for_cwd and specialised_job_for_cwd["ctx"]
                ), specialised_job_for_cwd
                assert (
                    "cwd" in specialised_job_for_cwd["ctx"]
                    and specialised_job_for_cwd["ctx"]["cwd"]
                ), specialised_job_for_cwd["ctx"].keys()
                specialised_job_for_cwd["ctx"]["cwd"] = cwd

                # add the last directory name from the 'cwd' path as a tag for
                # easy reference to the job-task by its path
                when: JobWhen = specialised_job_for_cwd.get("when", {})
                when["tags"] = set(when.get("tags", set()))
                cwd_path: pathlib.Path = pathlib.Path(cwd)
                when["tags"].add(cwd_path.name)
                specialised_job_for_cwd["when"] = when
                specialised_job_for_cwd["ctx"]["cwd"] = cwd

                # update the label to reflect the specialisation
                specialised_job_for_cwd["label"] = f"{job['label']}({cwd})"
                generated_jobs.append(specialised_job_for_cwd)

        for generated_job in generated_jobs:
            _parse_job(
                cfg_filepath,
                generated_job,
                in_out_tags,
                in_out_jobs_by_phase,
                in_out_job_names,
                in_out_phases,
                phase_order,
            )
    except KeyError as err:
        raise ValueError(
            f"job config entry is missing '{err.args[0]}' data. Have {job}"
        ) from err


def parse_config(config: Config, cfg_filepath: pathlib.Path) -> ConfigMetadata:
    """Validates and restructure the config to make it more convenient to use."""
    jobs_by_phase: PhaseGroupedJobs = defaultdict(list)
    job_names: JobNames = set()
    job_phases: JobPhases = set()
    tags: JobTags = set()
    entry: ConfigNodes
    seen_global: bool = False
    phase_order: OrderedPhases = ()
    options: OptionConfigs = ()
    file_filters: TagFileFilters = {}

    # first search for the global config
    for entry in config:
        # we apply a type-ignore here as we know (for now) that jobs have "job"
        # keys and global configs have "global" keys
        isinstance_job: bool = "job" in entry
        if isinstance_job:
            continue

        # we apply a type-ignore here as we know (for now) that jobs have "job"
        # keys and global configs have "global" keys
        isinstance_global: bool = "config" in entry
        if isinstance_global:
            if seen_global:
                raise ValueError(
                    "Found two global config entries, expected only one 'config' section. "
                    f"second one is {entry}"
                )
            seen_global = True
            global_entry: GlobalSerialisedConfig = entry  # type: ignore  # see above
            global_config: GlobalConfig = global_entry["config"]
            phase_order, options, file_filters = _parse_global_config(global_config)
            continue

        # not a global or a job entry, what is it
        raise RuntimeError(f"invalid 'job' or 'global' config entry, {entry}")

    if not phase_order:
        log("WARNING: phase ordering not configured! Runs will be non-deterministic!")
        phase_order = tuple(job_phases)

    # now parse out the job_configs
    for entry in config:
        isinstance_job_2: bool = "job" in entry
        if not isinstance_job_2:
            continue

        job_entry: JobSerialisedConfig = entry  # type: ignore  # see above
        job: JobConfig = job_entry["job"]
        parse_job_config(
            cfg_filepath,
            job,
            in_out_tags=tags,
            in_out_jobs_by_phase=jobs_by_phase,
            in_out_job_names=job_names,
            in_out_phases=job_phases,
            phase_order=phase_order,
        )

    # tags = tags.union(("python", "es", "firebase_funcs"))
    return ConfigMetadata(
        cfg_filepath,
        phase_order,
        options,
        file_filters,
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    )
