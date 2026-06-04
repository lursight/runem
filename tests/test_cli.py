from unittest.mock import Mock, patch

import pytest

import runem.cli


@patch(
    "runem.cli.timed_main",
    return_value=None,
)
def test_main(patched_main: Mock) -> None:
    runem.cli.main()
    patched_main.assert_called_once()


@patch("runem.cli.timed_main", return_value=None)
@patch("runem.cli.help_agents_text", return_value="agent help")
@patch("runem.cli.sys.argv", ["runem", "--help-agents"])
def test_main_help_agents(
    patched_help_agents_text: Mock,
    patched_main: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runem.cli.main()

    patched_help_agents_text.assert_called_once()
    patched_main.assert_not_called()
    assert capsys.readouterr().out == "agent help\n"


@patch("runem.cli.timed_main", return_value=None)
@patch("runem.cli.sys.argv", ["runem", "--help-agents"])
def test_main_help_agents_actual_content(
    patched_main: Mock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runem.cli.main()

    patched_main.assert_not_called()
    assert capsys.readouterr().out.startswith("runem agent integration\n")
