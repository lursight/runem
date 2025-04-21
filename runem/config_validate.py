import pathlib
import typing

from runem.log import error, log
from runem.types.errors import SystemExitBad
from runem.yaml_utils import load_yaml_object
from runem.yaml_validation import ValidationErrors, validate_yaml


def _load_runem_schema() -> typing.Any:
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


def validate_runem_file(
    cfg_filepath: pathlib.Path,
    all_config: typing.Any,
) -> None:
    """Validates the config Loader object against the runem schema.

    Exits if the files does not validate.
    """
    schema: typing.Any = _load_runem_schema()
    errors: ValidationErrors = validate_yaml(all_config, schema)
    if not errors:
        # aok
        return

    error(f"failed to validate runem config [yellow]{cfg_filepath}[/yellow]")
    for err in errors:
        path = ".".join(map(str, err.path)) or "<root>"
        log(f" [yellow]{path}[/yellow]: {err.message}")
    raise SystemExit("Config validation failed.")
