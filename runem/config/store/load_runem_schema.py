import pathlib
import typing

from runem.config.store.yaml_utils import load_yaml_object
from runem.log import error
from runem.types.errors import SystemExitBad


def load_runem_schema() -> typing.Any:
    """Loads and returns the yaml schema for runem.

    Returns:
        Any: the Draft202012Validator conformant schema.
    """
    schema_path: pathlib.Path = pathlib.Path(__file__).with_name("schema.yml")
    if not schema_path.exists():
        error(
            (
                "runem schema file not found, cannot continue! "
                f"Is the install corrupt? {schema_path}"
            )
        )
        raise SystemExitBad(1)
    schema: typing.Any = load_yaml_object(schema_path)
    return schema
