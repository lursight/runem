import argparse
import pathlib
import typing
from collections import defaultdict

from runem.hook_manager import HookManager
from runem.informative_dict import InformativeDict
from runem.types.common import JobNames, JobPhases, JobTags, OrderedPhases, PhaseName
from runem.types.filters import TagFileFilters
from runem.types.hooks import HookName
from runem.types.options import OptionsWritable
from runem.types.runem_config import OptionConfigs, PhaseGroupedJobs
from runem.types.types_jobs import HookSpecificKwargs


class ConfigMetadata:
    """Full metadata about what can and should be run."""

    phases: OrderedPhases  # the phases and orders to run them in
    options_config: OptionConfigs  # the options to add to the cli and pass to jobs
    file_filters: TagFileFilters  # which files to get for which tag
    hook_manager: "HookManager"  # the hooks register for the run
    jobs: PhaseGroupedJobs  # the jobs to be run ordered by phase
    all_job_names: JobNames  # the set of job-names
    all_job_phases: JobPhases  # the set of job-phases (should be subset of 'phases')
    all_job_tags: JobTags  # the set of job-tags (used for filtering)

    options: OptionsWritable  # the final configured options to pass to jobs

    args: argparse.Namespace  # the raw cli args, probably missing information
    jobs_to_run: JobNames  # superset of job-name candidates to run, from cli+config
    phases_to_run: JobPhases  # superset of phase candidates to run, from cli+config
    tags_to_run: JobTags  # superset of tag-candidates to run, from cli+config
    tags_to_avoid: JobTags  # superset of tag-withhold to NOT run, from cli+config

    def __init__(
        self,
        cfg_filepath: pathlib.Path,
        args: argparse.Namespace,
    ) -> None:
        self.cfg_filepath = cfg_filepath
        self.args = args

        self.phases = ()  # phases
        self.options_config = ()  # options_config
        self.file_filters = {}  # file_filters
        # initialise all the registered call-back hooks
        self.hook_manager = HookManager()
        self.jobs = defaultdict(list)
        self.all_job_names = set()  # all_job_names
        self.all_job_phases = set()  # all_job_phases
        self.all_job_tags = set()  # all_job_tags

        self.options = InformativeDict()  # shows useful errors on bad-option lookups

        self.jobs_to_run = set()  # will be defined after cli arg parsing
        self.phases_to_run = set()  # will be defined after cli arg parsing
        self.tags_to_run = set()  # will be defined after cli arg parsing
        self.tags_to_avoid = set()  # will be defined after cli arg parsing

    def set_cli_data(
        self,
        args: argparse.Namespace,
    ) -> None:
        self.args = args

        self._initialise_options(args)

        # apply the cli filters to produce the high-level requirements. These will be used
        # to further filter the jobs.
        self.jobs_to_run = set(args.jobs).difference(args.jobs_excluded)
        self.tags_to_run = set(args.tags).difference(args.tags_excluded)
        self.tags_to_avoid = set(args.tags_excluded)
        self.phases_to_run = set(args.phases).difference(args.phases_excluded)

    def invoke_hooks(
        self,
        hook_name: HookName,
        **kwargs: typing.Unpack[HookSpecificKwargs],
    ) -> None:
        root_dir = self.cfg_filepath.parent
        assert "root_dir" not in kwargs, "we auto-add 'root_dir' to hooks"
        kwargs["root_dir"] = root_dir
        self.hook_manager.invoke_hooks(
            hook_name,
            self,
            **kwargs,
        )

    def default_phase(self) -> PhaseName:
        return self.phases[0]  # default to the first phase

    def _initialise_options(
        self,
        args: argparse.Namespace,
    ) -> None:
        """Initialises the set of options to use for this run.

        Sets the options dictionary
        """
        options: OptionsWritable = InformativeDict(
            {option["name"]: option["default"] for option in self.options_config}
        )
        if self.options_config and args.overrides_on:  # pragma: no branch
            for option_name in args.overrides_on:  # pragma: no branch
                options[option_name] = True
        if self.options_config and args.overrides_off:  # pragma: no branch
            for option_name in args.overrides_off:
                options[option_name] = False
        self.options = options
