import typing

from runem.run_command import run_command
from runem.runem import Options


def _job_spellcheck(
    options: Options,
    es_files: typing.List[str],
    verbose: bool = False,
    **kwargs: typing.Any,
) -> None:
    es_spellcheck = ["yarn", "run", "spellCheck"]
    run_command("spellcheck", es_spellcheck, verbose)
