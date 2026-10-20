import pathlib
from datetime import timedelta

from typing_extensions import Unpack

from runem.types import HookKwargs


def _on_exit_hook(
    **kwargs: Unpack[HookKwargs],
) -> None:
    """A noddy hook: logs wall-clock time saved to .times.log in project root."""
    assert "wall_clock_time_saved" in kwargs
    wall_clock_time_saved: timedelta = kwargs["wall_clock_time_saved"]
    # Prefer explicit hook context (root_dir) when provided; else root_path from job kwargs.
    root_dir: pathlib.Path = kwargs.get("root_dir") or kwargs["root_path"]
    assert (root_dir / ".runem.yml").exists()
    times_log: pathlib.Path = root_dir / ".times.log"
    with times_log.open("a", encoding="utf-8") as file:
        file.write(f"{str(wall_clock_time_saved.total_seconds())}\n")
