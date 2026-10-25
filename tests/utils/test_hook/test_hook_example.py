from runem.hook.hook_example import _on_exit_hook_example
from runem.hook.specs.on_exit import ArgsOnExit

# pylint: disable=protected-access


def test_on_exit_hook_example() -> None:
    kwargs: ArgsOnExit = {"a": "a"}  # type:ignore
    _on_exit_hook_example(**kwargs)
