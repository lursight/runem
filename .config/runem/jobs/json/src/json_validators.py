import pathlib

from typing_extensions import Unpack

from runem.run_command import run_command
from runem.types import FilePathList, JobKwargs


def _json_validate(
    **kwargs: Unpack[JobKwargs],
) -> None:
    label = kwargs["label"]
    json_files: FilePathList = kwargs["file_list"]
    json_with_comments = (
        "cspell.json",
        "tsconfig.spec.json",
        "launch.json",
        "settings.json",
    )
    for json_file in json_files:
        json_path = pathlib.Path(json_file)
        if not json_path.exists():
            raise RuntimeError(
                f"could not find '{str(json_path)}, in {pathlib.Path('.').absolute()}"
            )
        if json_path.name in json_with_comments:
            # until we use a validator that allows comments in json, skip these
            continue

        cmd = ["python", "-m", "json.tool", f"{json_file}"]
        kwargs["label"] = f"{label} {json_file}"
        run_command(cmd=cmd, **kwargs)
