import pathlib
import typing

from run_test.test_runner.run_command import run_command

FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
OptionName = str
OptionValue = bool
Options = typing.Dict[OptionName, OptionValue]


def _json_validate(
    options: Options,
    json_files: FilePathList,
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    json_with_comments = ("cspell.json", "tsconfig.spec.json")
    for json_file in json_files:
        if pathlib.Path(json_file).name in json_with_comments:
            # until we use a validator that allows comments in json, skip these
            continue
        cmd = ["python", "-m", "json.tool", f"{json_file}"]
        run_command("json validate", cmd, verbose=verbose)
