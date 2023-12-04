import argparse
import pathlib

from runem.types import (
    JobNames,
    JobPhases,
    JobTags,
    OptionConfigs,
    Options,
    OrderedPhases,
    PhaseGroupedJobs,
    TagFileFilters,
)


class ConfigMetadata:
    """Full metadata about what can and should be run."""

    phases: OrderedPhases  # the phases and orders to run them in
    options_config: OptionConfigs  # the options to add to the cli and pass to jobs
    file_filters: TagFileFilters  # which files to get for which tag
    jobs: PhaseGroupedJobs  # the jobs to be run ordered by phase
    all_job_names: JobNames  # the set of job-names
    all_job_phases: JobPhases  # the set of job-phases (should be subset of 'phases')
    all_job_tags: JobTags  # the set of job-tags (used for filtering)

    options: Options  # the final configured options to pass to jobs

    args: argparse.Namespace  # the raw cli args, probably missing information
    jobs_to_run: JobNames  # superset of job-name candidates to run, from cli+config
    phases_to_run: JobPhases  # superset of phase candidates to run, from cli+config
    tags_to_run: JobTags  # superset of tag-candidates to run, from cli+config
    tags_to_avoid: JobTags  # superset of tag-withhold to NOT run, from cli+config

    def __init__(
        self,
        cfg_filepath: pathlib.Path,
        phases: OrderedPhases,
        options_config: OptionConfigs,
        file_filters: TagFileFilters,
        jobs: PhaseGroupedJobs,
        all_job_names: JobNames,
        all_job_phases: JobPhases,
        all_job_tags: JobTags,
    ) -> None:
        self.cfg_filepath = cfg_filepath
        self.phases = phases
        self.options_config = options_config
        self.file_filters = file_filters
        self.jobs = jobs
        self.all_job_names = all_job_names
        self.all_job_phases = all_job_phases
        self.all_job_tags = all_job_tags

        self.options = {}  # will be defined after cli argument parsing

        self.args = (
            argparse.Namespace()
        )  # the raw cli args, defined after argument parsing
        self.jobs_to_run = set()  # will be defined after cli arg parsing
        self.phases_to_run = set()  # will be defined after cli arg parsing
        self.tags_to_run = set()  # will be defined after cli arg parsing
        self.tags_to_avoid = set()  # will be defined after cli arg parsing

    def set_cli_data(
        self,
        args: argparse.Namespace,
        jobs_to_run: JobNames,
        phases_to_run: JobPhases,
        tags_to_run: JobTags,
        tags_to_avoid: JobTags,
        options: Options,
    ) -> None:
        self.options = options
        self.args = args
        self.jobs_to_run = jobs_to_run
        self.phases_to_run = phases_to_run
        self.tags_to_run = tags_to_run
        self.tags_to_avoid = tags_to_avoid
