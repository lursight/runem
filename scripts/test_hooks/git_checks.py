"""Git-related jobs for runem (e.g. check no NO COMMIT in messages since tracking)."""

import subprocess
from pathlib import Path

from typing_extensions import Unpack

from runem.run_command import RunCommandUnhandledError
from runem.types import JobKwargs
from runem.types.options import Options

# cspell:disable-next-line
NO_COMMIT_PHRASES = ["NO COMMIT", "NOCOMMIT"]  # *enforcing* the rule


def _job_check_branch_commit_messages(**kwargs: Unpack[JobKwargs]) -> None:
    """Validate commit-messages since tracking-branch.

    Raises RunCommandUnhandledError so runem reports this job as failed.
    """
    root_path: Path = kwargs["root_path"]
    options: Options = kwargs["options"]
    cwd = root_path

    if not options["pre-push"]:
        # We're not in a pre-push phase
        return

    result = subprocess.run(
        ["git", "rev-parse", "@{u}"],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=10,
        check=False,  # we will raise on non-zero exit
    )
    if result.returncode != 0:
        msg = (
            "check-no-commit: tracking branch is not set. "
            "Set one with e.g. 'git branch --set-upstream-to=origin/main'."
        )
        if result.stderr:
            msg = f"{msg}\n{result.stderr.strip()}"
        raise RunCommandUnhandledError(msg)

    upstream = result.stdout.strip()

    log_result = subprocess.run(
        ["git", "log", f"{upstream}..HEAD", "--format=%B"],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
        check=False,  # we will raise on non-zero exit
    )
    if log_result.returncode != 0:
        msg = "check-no-commit: failed to get commit log."
        if log_result.stderr:
            msg = f"{msg}\n{log_result.stderr.strip()}"
        raise RunCommandUnhandledError(msg)

    for bad_phrase in NO_COMMIT_PHRASES:
        if bad_phrase in log_result.stdout:
            raise RunCommandUnhandledError(
                f"check-no-commit: at least one commit since the tracking branch "
                f"contains '{bad_phrase}' in its message. Reword or amend."
            )
