import argparse
import os
import pathlib
import sys
import typing

from runem.config_metadata import ConfigMetadata
from runem.log import log
from runem.types import JobNames, OptionConfig, Options
from runem.utils import printable_set


def parse_args(
    config_metadata: ConfigMetadata, argv: typing.List[str]
) -> ConfigMetadata:
    """Parses the args and defines the filter inputs.

    Generates args based upon the config, parsing the cli args and return the filters to
    be used when selecting jobs.

    Returns the parsed args, the jobs_names_to_run, job_phases_to_run, job_tags_to_run
    """
    parser = argparse.ArgumentParser(description="Runs the Lursight Lang test-suite")

    job_group = parser.add_argument_group("jobs")
    all_job_names: JobNames = set(name for name in config_metadata.all_job_names)
    job_group.add_argument(
        "--jobs",
        dest="jobs",
        nargs="+",
        default=sorted(list(all_job_names)),
        help=(
            "List of job-names to run the given jobs. Other filters will modify this list. "
            f"Defaults to {printable_set(all_job_names)}"
        ),
        required=False,
    )
    job_group.add_argument(
        "--not-jobs",
        dest="jobs_excluded",
        nargs="+",
        default=[],
        help=(
            "List of job-names to NOT run. Defaults to empty. "
            f"Available options are: {printable_set((all_job_names))}"
        ),
        required=False,
    )

    phase_group = parser.add_argument_group("phases")
    phase_group.add_argument(
        "--phases",
        dest="phases",
        nargs="+",
        default=config_metadata.all_job_phases,
        help=(
            "Run only the phases passed in, and can be used to "
            "change the phase order. Phases are run in the order given. "
            f"Defaults to {printable_set(config_metadata.all_job_phases)}. "
        ),
        required=False,
    )
    phase_group.add_argument(
        "--not-phases",
        dest="phases_excluded",
        nargs="+",
        default=[],
        help=(
            "List of phases to NOT run. "
            "This option does not change the phase run order. "
            f"Options are '{sorted(config_metadata.all_job_phases)}'. "
        ),
        required=False,
    )

    tag_group = parser.add_argument_group("tags")
    tag_group.add_argument(
        "--tags",
        dest="tags",
        nargs="+",
        default=config_metadata.all_job_tags,
        help=(
            "Only jobs with the given tags. "
            f"Defaults to '{sorted(config_metadata.all_job_tags)}'."
        ),
        required=False,
    )
    tag_group.add_argument(
        "--not-tags",
        dest="tags_excluded",
        nargs="+",
        default=[],
        help=(
            "Removes one or more tags from the list of job tags to be run. "
            f"Options are '{sorted(config_metadata.all_job_tags)}'."
        ),
        required=False,
    )

    job_param_overrides_group = parser.add_argument_group(
        "job-param overrides",  # help="overrides default test params on all matching jobs"
    )
    _define_option_args(config_metadata, job_param_overrides_group)

    parser.add_argument(
        "--call-graphs",
        dest="generate_call_graphs",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    parser.add_argument(
        "--procs",
        "-j",
        # "-n",
        dest="procs",
        default=-1,
        help=(
            "the number of concurrent test jobs to run, -1 runs all test jobs at the same time "
            f"({os.cpu_count()} cores available)"
        ),
        required=False,
        type=int,
    )

    config_dir: pathlib.Path = config_metadata.cfg_filepath.parent
    parser.add_argument(
        "--root",
        dest="root_dir",
        default=config_dir,
        help=(
            "which dir to use as the base-dir for testing, "
            f"defaults to directory containing the config '{config_dir}'"
        ),
        required=False,
    )

    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    args = parser.parse_args(argv[1:])

    options: Options = initialise_options(config_metadata, args)

    if not _validate_filters(config_metadata, args):
        sys.exit(1)

    # apply the cli filters to produce the high-level requirements. These will be used
    # to further filter the jobs.
    jobs_to_run = set(args.jobs).difference(args.jobs_excluded)
    tags_to_run = set(args.tags).difference(args.tags_excluded)
    tags_to_avoid = set(args.tags_excluded)
    phases_to_run = set(args.phases).difference(args.phases_excluded)

    config_metadata.set_cli_data(
        args, jobs_to_run, phases_to_run, tags_to_run, tags_to_avoid, options
    )
    return config_metadata


def _validate_filters(
    config_metadata: ConfigMetadata,
    args: argparse.Namespace,
) -> bool:
    """Validates the command line filters given.

    returns True of success and False on failure
    """
    # validate the job-names passed in
    for name, name_list in (("--jobs", args.jobs), ("--not-jobs", args.jobs_excluded)):
        for job_name in name_list:
            if job_name not in config_metadata.all_job_names:
                log(
                    (
                        f"ERROR: invalid job-name '{job_name}' for {name}, "
                        f"choose from one of {printable_set(config_metadata.all_job_names)}"
                    )
                )
                return False

    # validate the tags passed in
    for name, tag_list in (("--tags", args.tags), ("--not-tags", args.tags_excluded)):
        for tag in tag_list:
            if tag not in config_metadata.all_job_tags:
                log(
                    (
                        f"ERROR: invalid tag '{tag}' for {name}, "
                        f"choose from one of {printable_set(config_metadata.all_job_tags)}"
                    )
                )
                return False

    # validate the phases passed in
    for name, phase_list in (
        ("--phases", args.phases),
        ("--not-phases", args.phases_excluded),
    ):
        for phase in phase_list:
            if phase not in config_metadata.all_job_phases:
                log(
                    (
                        f"ERROR: invalid phase '{phase}' for {name}, "
                        f"choose from one of {printable_set(config_metadata.all_job_phases)}"
                    )
                )
                return False
    return True


def initialise_options(
    config_metadata: ConfigMetadata,
    args: argparse.Namespace,
) -> Options:
    """Initialises and returns the set of options to use for this run.

    Returns the options dictionary
    """

    options: Options = {
        option["name"]: option["default"] for option in config_metadata.options_config
    }
    if config_metadata.options_config and args.overrides_on:  # pragma: no branch
        for option_name in args.overrides_on:  # pragma: no branch
            options[option_name] = True
    if config_metadata.options_config and args.overrides_off:  # pragma: no branch
        for option_name in args.overrides_off:
            options[option_name] = False
    return options


def _define_option_args(
    config_metadata: ConfigMetadata, job_param_overrides_group: argparse._ArgumentGroup
) -> None:
    option: OptionConfig
    for option in config_metadata.options_config:
        switch_name = option["name"].replace("_", "-").replace(" ", "-")

        aliases: typing.List[str] = []
        aliases_no: typing.List[str] = []
        if "aliases" in option and option["aliases"]:
            aliases = [
                _alias_to_switch(switch_name_alias)
                for switch_name_alias in option["aliases"]
            ]
            aliases_no = [
                _alias_to_switch(switch_name_alias, negatise=True)
                for switch_name_alias in option["aliases"]
            ]
        if "alias" in option and option["alias"]:
            aliases.append(_alias_to_switch(option["alias"]))
            aliases_no.append(_alias_to_switch(option["alias"], negatise=True))

        desc: typing.Optional[str] = None
        desc_for_off: typing.Optional[str] = None
        if "desc" in option:
            desc = option["desc"]
            desc_for_off = f"turn off {desc}"

        job_param_overrides_group.add_argument(
            f"--{switch_name}",
            *aliases,
            dest="overrides_on",
            action="append_const",
            const=option["name"],
            help=desc,
            required=False,
        )
        job_param_overrides_group.add_argument(
            f"--no-{switch_name}",
            *aliases_no,
            dest="overrides_off",
            action="append_const",
            const=option["name"],
            help=desc_for_off,
            required=False,
        )


def _alias_to_switch(switch_name_alias: str, negatise: bool = False) -> str:
    """Util function to generate a alias switch for argsparse."""
    single_letter_variant = not negatise and len(switch_name_alias) == 1
    if single_letter_variant:
        return f"-{switch_name_alias}"
    if negatise:
        return f"--no-{switch_name_alias}"
    return f"--{switch_name_alias}"
