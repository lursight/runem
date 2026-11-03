from typing_extensions import Unpack

from runem.hook.specs.on_exit import ArgsOnExit, on_exit_hook


@on_exit_hook
def _on_exit_hook_example(**kwargs: Unpack[ArgsOnExit]) -> None:
    """An example hook."""
