import pathlib
import typing

from runem.run_command import run_command

FilePathSerialise = str
FilePathList = typing.List[FilePathSerialise]
OptionName = str
OptionValue = bool
Options = typing.Dict[OptionName, OptionValue]


def _json_validate(
    **kwargs: typing.Any,
) -> None:
    label = kwargs["label"]
    json_files: FilePathList = kwargs["file_list"]
    json_with_comments = ("cspell.json", "tsconfig.spec.json")
    for json_file in json_files:
        if pathlib.Path(json_file).name in json_with_comments:
            # until we use a validator that allows comments in json, skip these
            continue
        cmd = ["python", "-m", "json.tool", f"{json_file}"]
        kwargs["label"] = f"{label} {json_file}"
        run_command(cmd=cmd, **kwargs)
