from typing import Any, List

from jsonschema import Draft202012Validator, ValidationError

# For now just return the raw ValidationErrors as a list
ValidationErrors = List[ValidationError]


def validate_yaml(yaml_data: Any, schema: Any) -> ValidationErrors:
    """Validates the give yaml data against the given schema, returning any errors.

    We use more future-looking validation so that we can have richer and more
    descriptive schema.

    Params:
        instance: JSON data loaded via `load_json` or similar
        schema: schema object compatible with a Draft202012Validator

    Returns:
        ValidationErrors: a sorted list of errors in the file, empty if none found
    """
    validator = Draft202012Validator(schema)
    errors: ValidationErrors = sorted(
        validator.iter_errors(yaml_data),
        key=lambda e: e.path,
    )

    return errors
