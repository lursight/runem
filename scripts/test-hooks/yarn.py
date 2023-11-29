import typing

from runem.run_command import run_command
from runem.runem import Options


def _job_spellcheck(
    **kwargs: typing.Any,
) -> None:
    es_spellcheck = ["yarn", "run", "spellCheck"]
    run_command(cmd=es_spellcheck, **kwargs)
