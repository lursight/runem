import argparse
import copy
import pathlib
import sys
import typing
from collections.abc import Iterable

from runem.config.config_metadata import ConfigMetadata
from runem.execute.job_wrapper import get_job_wrapper
from runem.hook.hook_manager import HookManager
from runem.hook.hook_name import HookName
from runem.job.job import Job
from runem.log import error, warn
from runem.types.common import (
    JobName,
    JobPhases,
    JobTags,
    PhaseName,
)
from runem.types.errors import FunctionNotFound, SystemExitBad
from runem.types.filters import TagFileFilter, TagFileFilters
from runem.types.runem_config import (
    Config,
    ConfigNodes,
    GlobalConfig,
    GlobalSerialisedConfig,
    HookConfig,
    HookSerialisedConfig,
    JobConfig,
    JobSerialisedConfig,
    JobWhen,
    OptionConfigs,
    TagFileFilterSerialised,
)


class _ConfigMetadataCollector:
    config: ConfigMetadata

    def __init__(self, config: ConfigMetadata) -> None:
        self.config = config

    def add_job(self, job_name: JobName, phase: PhaseName, job: JobConfig) -> None:
        self.config.hook_manager.invoke_on_job_add(
            metadata={
                "job": job,
            },
        )

        self.config.all_job_names.add(job_name)
        self.config.all_job_phases.add(phase)
        job_tags: typing.Optional[JobTags] = Job.get_job_tags(job)
        if job_tags:
            self.config.all_job_tags.update(job_tags)

        self.config.jobs[phase].append(job)


def _support_job_module(cfg_filepath: pathlib.Path) -> None:
    """Support `module` job-configs, by adding the .runem.yml dir to the sys.path.

    This allows dynamic import of the job-config.

    Dotted modules intentionally keep Python's project/environment import rules.
    Supporting arbitrary Python environments needs an explicit execution design;
    config fragments must not mutate ``sys.path`` with their own directories.
    """
    # Capture the ctx-path for `module` type jobs. Ensure we are using the
    # fully-qualified and resolved version of the path.
    new_import_ctx_path: str = str(
        cfg_filepath.parent.resolve(
            strict=True  # raise if any part of the parent dir is not found
        )
    )
    if new_import_ctx_path not in sys.path:  # ctx is not already configured.
        # prepend the config's path to the PYTHONPATH
        sys.path.insert(0, new_import_ctx_path)


def _parse_global_config(
    global_config: GlobalConfig,
    config_collector: _ConfigMetadataCollector,
) -> None:
    """Parses and validates a global-config entry read in from disk.

    Returns the phases in the order we want to run them
    """
    if "options" in global_config and global_config["options"]:
        options: OptionConfigs = tuple(
            option_serialised["option"]
            for option_serialised in global_config["options"]
        )
        config_collector.config.options_config = options

    if "files" in global_config and global_config["files"]:
        file_filter: TagFileFilterSerialised
        serialised_filters: typing.List[TagFileFilterSerialised] = global_config[
            "files"
        ]
        file_filters: TagFileFilters = {}
        for file_filter in serialised_filters:
            actual_filter: TagFileFilter = file_filter["filter"]
            tag = actual_filter["tag"]
            file_filters[tag] = actual_filter
        config_collector.config.file_filters = file_filters

    if "phases" in global_config:
        config_collector.config.phases = global_config["phases"]


def _parse_hook_config(
    hook: HookConfig,
    cfg_filepath: pathlib.Path,
    config_collector: _ConfigMetadataCollector,
    verbose: bool,
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
        error(f"Whilst loading hook '{str(hook['hook_name'])}'. {str(err)}")
        raise SystemExitBad(2) from err

    hook_name: HookName = hook["hook_name"]
    config_collector.config.hook_manager.register_hook(hook_name, hook, verbose=verbose)


def _parse_hook_entry(
    hook_entry: HookSerialisedConfig,
    config_collector: _ConfigMetadataCollector,
    cfg_filepath: pathlib.Path,
    verbose: bool,
) -> None:
    """Get the hook information, verifying validity."""
    hook: HookConfig = hook_entry["hook"]
    assert "hook_name" in hook
    _parse_hook_config(
        hook,
        config_collector=config_collector,
        cfg_filepath=cfg_filepath,
        verbose=verbose,
    )


def _parse_job(  # noqa: C901
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    config_collector: _ConfigMetadataCollector,
    warn_missing_phase: bool = True,
) -> None:
    """Parse an individual job."""
    job_name: str = Job.get_job_name(job)
    job_name_used = job_name in config_collector.config.all_job_names
    if job_name_used:
        error(
            "duplicate job label!"
            f"\t'{job['label']}' is used twice or more in {str(cfg_filepath)}"
        )
        sys.exit(1)

    try:
        # try and load the function _before_ we schedule it's execution
        get_job_wrapper(job, cfg_filepath)
    except FunctionNotFound as err:
        error(f"Whilst loading job '{job['label']}'. {str(err)}")
        raise SystemExitBad(2) from err

    try:
        phase_id: PhaseName = job["when"]["phase"]
    except KeyError:
        try:
            fallback_phase = config_collector.config.default_phase()
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
    config_collector.add_job(job_name=job_name, phase=phase_id, job=job)


def _parse_job_config(
    cfg_filepath: pathlib.Path,
    job: JobConfig,
    config_collector: _ConfigMetadataCollector,
    silent: bool = False,
) -> None:
    """Parses and validates a job-entry read in from disk."""
    try:
        # if there is more than one cwd, duplicate the job for each cwd
        generated_jobs: typing.List[JobConfig] = []
        have_ctw_cwd: bool = (("ctx" in job) and (job["ctx"] is not None)) and (
            ("cwd" in job["ctx"]) and (job["ctx"]["cwd"] is not None)
        )
        if (not have_ctw_cwd) or isinstance(
            job["ctx"]["cwd"],  # type: ignore # handled above
            str,
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
                config_collector,
                warn_missing_phase=(not silent),
            )
    except KeyError as err:
        raise ValueError(
            f"job config entry is missing '{err.args[0]}' data. Have {job}"
        ) from err


def _parse_config(  # noqa: C901 # pylint: disable=R0914
    config: Config,
    cfg_filepath: pathlib.Path,
    config_collector: _ConfigMetadataCollector,
    silent: bool = False,
    verbose: bool = False,
    hooks_only: bool = False,
) -> None:
    """Validates and restructure the config to make it more convenient to use."""
    job_phases: JobPhases = set()
    entry: ConfigNodes
    seen_global: bool = False

    # Support `module` dynamic imports
    _support_job_module(cfg_filepath)

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
            _parse_global_config(global_config, config_collector)
            continue

        # we apply a type-ignore here as we know (for now) that jobs have "job"
        # keys and global configs have "global" keys
        isinstance_hooks: bool = "hook" in entry
        if isinstance_hooks:
            hook_entry: HookSerialisedConfig = entry  # type: ignore  # see above
            _parse_hook_entry(
                hook_entry,
                config_collector,
                cfg_filepath,
                verbose=verbose,
            )

            # continue to the next element and do NOT error
            continue

        # not a global or a job entry, what is it
        raise RuntimeError(f"invalid 'job', 'hook, or 'global' config entry, {entry}")

    if not config_collector.config.phases:
        if not hooks_only:
            if silent:  # pragma: no cover
                pass
            else:
                warn("phase ordering not configured! Runs will be non-deterministic!")
            config_collector.config.phases = tuple(job_phases)

    # now parse out the job_configs
    for entry in config:
        isinstance_job_2: bool = "job" in entry
        if not isinstance_job_2:
            continue

        job_entry: JobSerialisedConfig = entry  # type: ignore  # see above
        job: JobConfig = job_entry["job"]
        _parse_job_config(
            cfg_filepath,
            job,
            config_collector,
            silent=silent,
        )


def _load_user_hooks_from_config(
    user_config: Config,
    cfg_filepath: pathlib.Path,
    config_collector: _ConfigMetadataCollector,
) -> None:
    _parse_config(
        user_config,
        cfg_filepath,
        config_collector,
        hooks_only=True,
    )


def load_config_metadata(
    config: Config,
    cfg_filepath: pathlib.Path,
    user_configs: typing.List[typing.Tuple[Config, pathlib.Path]],
    args: argparse.Namespace,
) -> ConfigMetadata:
    config_collector = _ConfigMetadataCollector(ConfigMetadata(cfg_filepath, args))

    user_config: Config
    user_config_path: pathlib.Path
    for user_config, user_config_path in user_configs:
        _load_user_hooks_from_config(
            user_config,
            user_config_path,
            config_collector,
        )
    _parse_config(
        config,
        cfg_filepath,
        config_collector,
        silent=args.silent,
        verbose=args.verbose,
    )

    config_collector.config.hook_manager.invoke_on_config_loaded(
        metadata={
            "config": config_collector.config.as_dict(),
        },
    )
    return config_collector.config
