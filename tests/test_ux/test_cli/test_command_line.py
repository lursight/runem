from pathlib import Path

import pytest

from runem.ux.cli.command_line import RunemArgsParse


def test_root_path_arg(tmp_path: Path) -> None:
    """Current unused! see the expected failure below.

    Update test_expected_failure_for_root_path_cli_arg if changing.
    """
    dummy_runem_cfg = tmp_path / "no exist"
    assert not dummy_runem_cfg.exists(), "should not be accessed during test"
    parse = RunemArgsParse(dummy_runem_cfg)
    parse.parse_early(["--root-path", str(dummy_runem_cfg.parent)])
    assert parse.args is not None
    assert parse.args.root_path == dummy_runem_cfg.parent


@pytest.mark.xfail
def test_expected_failure_for_root_path_cli_arg() -> None:
    """FIXME!

    Update test_root_path_arg if changing.
    """
    raise RuntimeError("`--root-path=<x>` is not wired in yet!")
