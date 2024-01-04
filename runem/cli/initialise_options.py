import argparse

from runem.config_metadata import ConfigMetadata
from runem.types import Options


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
