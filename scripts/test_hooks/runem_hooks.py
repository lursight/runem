import pathlib
from datetime import timedelta

from typing_extensions import Unpack

from runem.types import HookKwargs


def _on_exit_hook(
    **kwargs: Unpack[HookKwargs],
) -> None:
    """A noddy hook."""
    assert "wall_clock_time_saved" in kwargs
    wall_clock_time_saved: timedelta = kwargs["wall_clock_time_saved"]
    root_path: pathlib.Path = pathlib.Path(__file__).parent.parent.parent
    assert (root_path / ".runem.yml").exists()
    times_log: pathlib.Path = root_path / ".times.log"
    with times_log.open("a", encoding="utf-8") as file:
        file.write(f"{str(wall_clock_time_saved.total_seconds())}\n")
