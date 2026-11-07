import pathlib
import typing

from runem.config.store.load_runem_schema import load_runem_schema
from runem.config.store.yaml_validation import ValidationErrors, validate_yaml
from runem.log import error, log


def validate_runem_file(
    cfg_filepath: pathlib.Path,
    all_config: typing.Any,
) -> None:
    """Validates the config Loader object against the runem schema.

    Exits if the files does not validate.
    """
    schema: typing.Any = load_runem_schema()
    errors: ValidationErrors = validate_yaml(all_config, schema)
    if not errors:
        # aok
        return

    error(f"failed to validate runem config [yellow]{cfg_filepath}[/yellow]")
    for err in errors:
        path = ".".join(map(str, err.path)) or "<root>"
        log(f" [yellow]{path}[/yellow]: {err.message}")
    raise SystemExit("Config validation failed.")
