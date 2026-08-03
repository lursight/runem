import pathlib
import typing
from unittest.mock import Mock, patch

from markdown_jobs import (
    _job_markdown_lint,
    _job_markdown_prettier,
)

from runem.informative_dict import InformativeDict


def _job_kwargs(check_only: bool = False) -> typing.Dict[str, typing.Any]:
    return {
        "file_list": ["README.md", "HISTORY.md", "docs/quick_start.md"],
        "options": InformativeDict({"check-only": check_only}),
        "label": "markdown",
        "verbose": False,
    }


@patch("markdown_jobs.run_command")
def test_markdown_lint_uses_selected_files_and_ignores_history(
    mock_run_command: Mock,
) -> None:
    _job_markdown_lint(**_job_kwargs())

    mock_run_command.assert_called_once()
    assert mock_run_command.call_args.kwargs["cmd"] == [
        "yarn",
        "exec",
        "markdownlint-cli2",
        "README.md",
        "docs/quick_start.md",
    ]


@patch("markdown_jobs.run_command")
def test_markdown_prettier_writes_by_default(mock_run_command: Mock) -> None:
    _job_markdown_prettier(**_job_kwargs())

    assert mock_run_command.call_args.kwargs["cmd"][-1] == "--write"


@patch("markdown_jobs.run_command")
def test_markdown_prettier_checks_in_check_mode(mock_run_command: Mock) -> None:
    _job_markdown_prettier(**_job_kwargs(check_only=True))

    assert mock_run_command.call_args.kwargs["cmd"][-1] == "--check"
    assert "--write" not in mock_run_command.call_args.kwargs["cmd"]


@patch("markdown_jobs.run_command")
def test_markdown_jobs_skip_when_only_ignored_files_are_selected(
    mock_run_command: Mock,
) -> None:
    kwargs = _job_kwargs()
    kwargs["file_list"] = [pathlib.Path("HISTORY.md")]

    _job_markdown_lint(**kwargs)
    _job_markdown_prettier(**kwargs)

    mock_run_command.assert_not_called()
