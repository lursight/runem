import pathlib
import typing

import yaml


def load_yaml_object(yaml_file: pathlib.Path) -> typing.Any:
    """Loads using full_load, a yaml file.

    This is likely to have safety concerns in non-trusted projects.

    Returns:
        YAML Loader object: the full PyYAML loader object.
    """
    # Do a full, untrusted load of the runem config
    # TODO: work out safety concerns of this
    with yaml_file.open("r", encoding="utf-8") as file_handle:
        full_yaml_object: typing.Any = yaml.full_load(file_handle)
    return full_yaml_object
