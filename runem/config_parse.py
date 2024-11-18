import copy
import pathlib
import sys
import typing
from collections import defaultdict
from collections.abc import Iterable

from runem.config_metadata import ConfigMetadata
from runem.hook_manager import HookManager
from runem.job import Job
from runem.job_wrapper import get_job_wrapper
from runem.log import error, log, warn
from runem.types.common import JobNames, JobPhases, JobTags, OrderedPhases, PhaseName
from runem.types.errors import FunctionNotFound
from runem.types.filters import TagFileFilter, TagFileFilters
from runem.types.hooks import HookName
from runem.types.runem_config import (
    Config,
    ConfigNodes,
    GlobalConfig,
    GlobalSerialisedConfig,
    HookConfig,
    Hooks,
    HookSerialisedConfig,
    JobConfig,
    JobSerialisedConfig,
    JobWhen,
    OptionConfigs,
    PhaseGroupedJobs,
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


def parse_hook_config(
    hook: HookConfig,
    cfg_filepath: pathlib.Path,
) -> None:
    """Get the hook information, verifying validity."""
    try:
        if not HookManager.is_valid_hook_name(hook["hook_name"]):
            raise ValueError(
                f"invalid hook-name '{str(hook['hook_name'])}'. "
                f"Valid hook names are: {[hook.value for hook in HookName]}"
            )
        # cast the hook-name to a HookName type
        hook["hook_name"] = HookName(hook["hook_name"])
        get_job_wrapper(hook, cfg_filepath)
    except KeyError as err:
        raise ValueError(
            f"hook config entry is missing '{err.args[0]}' key. Have {tuple(hook.keys())}"
        ) from err
    except FunctionNotFound as err:
        raise FunctionNotFound(
            f"Whilst loading job '{str(hook['hook_name'])}'. {str(err)}"
        ) from err


def _parse_job(  # noqa: C901
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    in_out_tags: JobTags,
    in_out_jobs_by_phase: PhaseGroupedJobs,
    in_out_job_names: JobNames,
    in_out_phases: JobPhases,
    phase_order: OrderedPhases,
    warn_missing_phase: bool = True,
) -> None:
    """Parse an individual job."""
    job_name: str = Job.get_job_name(job)
    job_names_used = job_name in in_out_job_names
    if job_names_used:
        error(
            "duplicate job label!"
            f"\t'{job['label']}' is used twice or more in {str(cfg_filepath)}"
        )
        sys.exit(1)

    try:
        # try and load the function _before_ we schedule it's execution
        get_job_wrapper(job, cfg_filepath)
    except FunctionNotFound as err:
        raise FunctionNotFound(
            f"Whilst loading job '{job['label']}'. {str(err)}"
        ) from err

    try:
        phase_id: PhaseName = job["when"]["phase"]
    except KeyError:
        try:
            fallback_phase = phase_order[0]
            if warn_missing_phase:
                warn(f"no phase found for '{job_name}', using '{fallback_phase}'")
        except IndexError:
            fallback_phase = "<NO PHASES FOUND>"
            if warn_missing_phase:
                warn(
                    (
                        f"no phases found for '{job_name}', "
                        f"or in '{str(cfg_filepath)}', "
                        f"using '{fallback_phase}'"
                    )
                )
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


def parse_config(
    config: Config, cfg_filepath: pathlib.Path, hooks_only: bool = False
) -> typing.Tuple[
    Hooks,  # hooks:
    OrderedPhases,  # phase_order:
    OptionConfigs,  # options:
    TagFileFilters,  # file_filters:
    PhaseGroupedJobs,  # jobs_by_phase:
    JobNames,  # job_names:
    JobPhases,  # job_phases:
    JobTags,  # tags:
]:
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
    hooks: Hooks = defaultdict(list)

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

        # we apply a type-ignore here as we know (for now) that jobs have "job"
        # keys and global configs have "global" keys
        isinstance_hooks: bool = "hook" in entry
        if isinstance_hooks:
            hook_entry: HookSerialisedConfig = entry  # type: ignore  # see above
            hook: HookConfig = hook_entry["hook"]
            parse_hook_config(hook, cfg_filepath)

            # if we get here we have validated the hook, add it to the hooks list
            hook_name: HookName = hook["hook_name"]
            hooks[hook_name].append(hook)

            # continue to the next element and do NOT error
            continue

        # not a global or a job entry, what is it
        raise RuntimeError(f"invalid 'job', 'hook, or 'global' config entry, {entry}")

    if not phase_order:
        if not hooks_only:
            warn("phase ordering not configured! Runs will be non-deterministic!")
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
    return (
        hooks,
        phase_order,
        options,
        file_filters,
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    )


def generate_config(
    cfg_filepath: pathlib.Path,
    hooks: Hooks,
    phase_order: OrderedPhases,
    verbose: bool,
    options: OptionConfigs,
    file_filters: TagFileFilters,
    jobs_by_phase: PhaseGroupedJobs,
    job_names: JobNames,
    job_phases: JobPhases,
    tags: JobTags,
) -> ConfigMetadata:
    """Constructs the ConfigMetadata from parsed config parts."""
    return ConfigMetadata(
        cfg_filepath,
        phase_order,
        options,
        file_filters,
        HookManager(hooks, verbose),
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    )


def _load_user_hooks_from_config(
    user_config: Config, cfg_filepath: pathlib.Path
) -> Hooks:
    hooks: Hooks
    (
        hooks,
        _,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = parse_config(user_config, cfg_filepath, hooks_only=True)
    return hooks


def load_config_metadata(
    config: Config,
    cfg_filepath: pathlib.Path,
    user_configs: typing.List[typing.Tuple[Config, pathlib.Path]],
    verbose: bool = False,
) -> ConfigMetadata:
    hooks: Hooks
    phase_order: OrderedPhases
    options: OptionConfigs
    file_filters: TagFileFilters
    jobs_by_phase: PhaseGroupedJobs
    job_names: JobNames
    job_phases: JobPhases
    tags: JobTags
    (
        hooks,
        phase_order,
        options,
        file_filters,
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    ) = parse_config(config, cfg_filepath)

    user_config: Config
    user_config_path: pathlib.Path
    for user_config, user_config_path in user_configs:
        user_hooks: Hooks = _load_user_hooks_from_config(user_config, user_config_path)
        if user_hooks:
            if verbose:
                log(f"hooks: loading user hooks from '{str(user_config_path)}'")
        hook_name: HookName
        hooks_for_name: typing.List[HookConfig]
        for hook_name, hooks_for_name in user_hooks.items():
            hooks[hook_name].extend(hooks_for_name)
            if verbose:
                log(
                    f"hooks:\tadded {len(hooks_for_name)} user hooks for '{str(hook_name)}'"
                )

    return generate_config(
        cfg_filepath,
        hooks,
        phase_order,
        verbose,
        options,
        file_filters,
        jobs_by_phase,
        job_names,
        job_phases,
        tags,
    )
