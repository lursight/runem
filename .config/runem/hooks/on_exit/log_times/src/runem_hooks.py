import pathlib
from datetime import timedelta

from typing_extensions import Unpack

from runem.hook.hook_args import HookArgs
from runem.hook.specs.on_exit import ArgsOnExit, on_exit_hook


@on_exit_hook
def _on_exit_hook(
    **kwargs: Unpack[ArgsOnExit],
) -> None:
    """A noddy hook: logs wall-clock time saved to .times.log in project root."""
    assert "metadata" in kwargs
    metadata: HookArgs.OnExit = kwargs["metadata"]
    assert metadata is not None
    assert "wall_clock_time_saved" in metadata
    wall_clock_time_saved: timedelta = metadata["wall_clock_time_saved"]
    # Prefer explicit hook context (root_dir) when provided; else root_path from job kwargs.
    root_path: pathlib.Path = kwargs["root_path"]
    assert (root_path / ".runem.yml").exists()
    times_log: pathlib.Path = root_path / ".times.log"
    with times_log.open("a", encoding="utf-8") as file:
        file.write(f"{str(wall_clock_time_saved.total_seconds())}\n")
