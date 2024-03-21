import pathlib
import typing
from datetime import timedelta


def _on_exit_hook(
    wall_clock_time_saved: timedelta,
    **kwargs: typing.Any,
) -> None:
    """A noddy hook."""
    root_path: pathlib.Path = pathlib.Path(__file__).parent.parent.parent
    assert (root_path / ".runem.yml").exists()
    times_log: pathlib.Path = root_path / ".times.log"
    with times_log.open("a", encoding="utf-8") as file:
        file.write(f"{str(wall_clock_time_saved.total_seconds())}\n")
