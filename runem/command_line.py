import argparse
import os
import pathlib
import sys
import typing

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.log import error, log
from runem.runem_version import get_runem_version
from runem.types.common import JobNames
from runem.types.options import OptionsWritable
from runem.types.runem_config import OptionConfig
from runem.utils import printable_set


class HelpFormatterFixedWidth(argparse.HelpFormatter):
    """This works around test issues via constant width helo output.

    This ensures that we get more constant for help-text by fixing the width to
    something reasonable.
    """

    def __init__(self, prog: typing.Any) -> None:
        # Override the default width with a fixed width, for tests.
        super().__init__(
            prog,
            # Pretty wide so we do not get wrapping on directories
            # or process-count output.
            width=1000,
        )


def _get_argparse_help_formatter() -> typing.Any:
    """Returns a help-formatter for argparse.

    This is for tests only to fake terminals of a constant with when rendering help
    output.
    """
    # Check environment variable to see if we're in tests and need a fixed width
    # help output.
    use_fixed_width = os.getenv("RUNEM_FIXED_HELP_WIDTH", None)

    if use_fixed_width:
        # Use custom formatter with the width specified in the environment variable
        return (
            lambda prog: HelpFormatterFixedWidth(  # pylint: disable=unnecessary-lambda
                prog
            )
        )

    # Use default formatter
    return argparse.HelpFormatter


def parse_args(
    config_metadata: ConfigMetadata, argv: typing.List[str]
) -> ConfigMetadata:
    """Parses the args and defines the filter inputs.

    Generates args based upon the config, parsing the cli args and return the filters to
    be used when selecting jobs.

    Returns the parsed args, the jobs_names_to_run, job_phases_to_run, job_tags_to_run
    """
    parser = argparse.ArgumentParser(
        add_help=False,
        description="Runs the Lursight Lang test-suite",
        formatter_class=_get_argparse_help_formatter(),
    )
    parser.add_argument(
        "-H", "--help", action="help", help="show this help message and exit"
    )

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
        "-f",
        "--modified-files",
        dest="check_modified_files",
        help="only use files that have changed",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    parser.add_argument(
        "-h",
        "--git-head-files",
        dest="check_head_files",
        help="fast run of files",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )
    parser.add_argument(
        "--always-files",
        dest="always_files",
        help=(
            "list of paths/files to always check (overriding -f/-h), if the path "
            "matches the filter regex and if file-paths exist"
        ),
        nargs="+",
        default=None,
        required=False,
    )

    parser.add_argument(
        "--git-files-since-branch",
        dest="git_since_branch",
        help=(
            "Get the list of paths/files changed between a branch, e.g., since "
            "'origin/main'. Useful for checking files changed before pushing."
        ),
        default=None,  # Default to None if no branch is specified
        required=False,  # Not required, users may not want to specify a branch
        type=str,  # Accepts a string input representing the branch name
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

    config_dir: pathlib.Path = _get_config_dir(config_metadata)
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
        "--root-show",
        dest="show_root_path_and_exit",
        help="show the root-path of runem and exit",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    parser.add_argument(
        "--spinner",
        dest="show_spinner",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Whether to show the progress spinner or not. "
            "Helps reduce log-spam in ci/cd."
        ),
        required=False,
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        help="runs runem in in verbose mode, and streams jobs stdout/stderr to console",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    parser.add_argument(
        "--version",
        "-v",
        dest="show_version_and_exit",
        help="show the version of runem and exit",
        action=argparse.BooleanOptionalAction,
        default=False,
        required=False,
    )

    args = parser.parse_args(argv[1:])

    if args.show_root_path_and_exit:
        log(str(config_metadata.cfg_filepath.parent), decorate=False)
        # cleanly exit
        sys.exit(0)

    if args.show_version_and_exit:
        log(str(get_runem_version()), decorate=False)
        # cleanly exit
        sys.exit(0)

    options: OptionsWritable = initialise_options(config_metadata, args)

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


def _get_config_dir(config_metadata: ConfigMetadata) -> pathlib.Path:
    """A function to get the path, that we can mock in tests."""
    return config_metadata.cfg_filepath.parent


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
                error(
                    (
                        f"invalid job-name '{job_name}' for {name}, "
                        f"choose from one of {printable_set(config_metadata.all_job_names)}"
                    )
                )
                return False

    # validate the tags passed in
    for name, tag_list in (("--tags", args.tags), ("--not-tags", args.tags_excluded)):
        for tag in tag_list:
            if tag not in config_metadata.all_job_tags:
                error(
                    (
                        f"invalid tag '{tag}' for {name}, "
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
                error(
                    (
                        f"invalid phase '{phase}' for {name}, "
                        f"choose from one of {printable_set(config_metadata.all_job_phases)}"
                    )
                )
                return False
    return True


def initialise_options(
    config_metadata: ConfigMetadata,
    args: argparse.Namespace,
) -> OptionsWritable:
    """Initialises and returns the set of options to use for this run.

    Returns the options dictionary
    """

    options: OptionsWritable = InformativeDict(
        {option["name"]: option["default"] for option in config_metadata.options_config}
    )
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
    """Util function to generate a alias switch for argparse."""
    single_letter_variant = not negatise and len(switch_name_alias) == 1
    if single_letter_variant:
        return f"-{switch_name_alias}"
    if negatise:
        return f"--no-{switch_name_alias}"
    return f"--{switch_name_alias}"
