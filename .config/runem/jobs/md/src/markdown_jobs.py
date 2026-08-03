"""Markdown linting and formatting jobs for runem."""

import pathlib
import typing

from typing_extensions import Unpack

from runem.run_command import run_command
from runem.types import FilePathList, JobKwargs, Options

MARKDOWN_IGNORE_LIST: typing.Tuple[str, ...] = ("HISTORY.md",)


def _get_markdown_files(file_list: FilePathList) -> FilePathList:
    """Return Markdown files that are not in the shared ignore list."""
    return [
        file_path
        for file_path in file_list
        if pathlib.Path(file_path).name not in MARKDOWN_IGNORE_LIST
    ]


def _job_markdown_lint(**kwargs: Unpack[JobKwargs]) -> None:
    """Lint the selected Markdown files without modifying them."""
    markdown_files = _get_markdown_files(kwargs["file_list"])
    if not markdown_files:
        return

    markdownlint_cmd = [
        "yarn",
        "exec",
        "markdownlint-cli2",
        *markdown_files,
    ]
    run_command(cmd=markdownlint_cmd, **kwargs)


def _job_markdown_prettier(**kwargs: Unpack[JobKwargs]) -> None:
    """Format Markdown, or check formatting when runem is in check mode."""
    markdown_files = _get_markdown_files(kwargs["file_list"])
    if not markdown_files:
        return

    options: Options = kwargs["options"]
    write_option = "--check" if options["check-only"] else "--write"
    prettier_cmd = [
        "yarn",
        "run",
        "prettier",
        *markdown_files,
        write_option,
    ]
    run_command(cmd=prettier_cmd, **kwargs)
