import argparse

from runem.config_metadata import ConfigMetadata
from runem.informative_dict import InformativeDict
from runem.types.options import OptionsWritable


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
