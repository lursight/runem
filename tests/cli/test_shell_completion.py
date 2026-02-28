import argparse
from unittest.mock import MagicMock, patch

from runem.command_line import _enable_shell_completion, _static_values_completer


def test_static_values_completer_filters_by_prefix() -> None:
    completer = _static_values_completer(("job_a", "job_b", "tag_a"))
    assert completer("job") == ["job_a", "job_b"]


def test_enable_shell_completion_without_argcomplete() -> None:
    parser = argparse.ArgumentParser()
    with patch(
        "runem.command_line.importlib.import_module",
        side_effect=ImportError,
    ):
        _enable_shell_completion(parser)


def test_enable_shell_completion_with_argcomplete() -> None:
    parser = argparse.ArgumentParser()
    argcomplete_module = MagicMock()
    with patch(
        "runem.command_line.importlib.import_module",
        return_value=argcomplete_module,
    ):
        _enable_shell_completion(parser)
    argcomplete_module.autocomplete.assert_called_once_with(parser)
