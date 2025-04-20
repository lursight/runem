"""tests/test_config_validate.py.

Unit‑tests for `runem.config_validate`.

Coverage
========
1. `_load_runem_schema`
   • success path (schema present)
   • error path  (schema missing → SystemExitBad)

2. `validate_runem_file`
   • happy path   (no validation errors)
   • failure path (≥1 validation error → SystemExit, correct logging)

Design notes
============
* All I/O is faked with `monkeypatch`; no real files created in package dirs.
* Dummy error objects stand‑in for `jsonschema.ValidationError` to keep deps thin.
* Each test asserts **behaviour**, not internals.
"""
# pylint: disable=protected-access

from __future__ import annotations

import pathlib
from typing import List, Union

import pytest

# --------------------------------------------------------------------------- #
# Test helpers
# --------------------------------------------------------------------------- #
import runem.config_validate as uut  # unit under test


class _DummyErr:  # pylint: disable=too-few-public-methods
    """Minimal substitute for jsonschema.ValidationError."""

    def __init__(self, path: List[Union[str, int]], message: str) -> None:
        self.path = path
        self.message = message


# --------------------------------------------------------------------------- #
# _load_runem_schema
# --------------------------------------------------------------------------- #


def test_load_runem_schema_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns loaded schema when file exists."""
    sentinel: object = object()

    monkeypatch.setattr(
        uut.pathlib.Path,  # type: ignore[attr-defined]
        "exists",
        lambda self: True,  # noqa: ANN001
        raising=False,
    )
    monkeypatch.setattr(uut, "load_yaml_object", lambda _: sentinel)

    assert uut._load_runem_schema() is sentinel  # pyright: ignore [private‑access]


def test_load_runem_schema_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raises `SystemExitBad` and logs when schema file is absent."""
    calls: list[str] = []

    monkeypatch.setattr(
        uut.pathlib.Path,  # type: ignore[attr-defined]
        "exists",
        lambda self: False,  # noqa: ANN001
        raising=False,
    )
    monkeypatch.setattr(uut, "error", lambda msg: calls.append(str(msg)))

    with pytest.raises(uut.SystemExitBad):  # type: ignore[attr-defined]
        uut._load_runem_schema()

    assert calls and "schema file not found" in calls[0]


# --------------------------------------------------------------------------- #
# validate_runem_file
# --------------------------------------------------------------------------- #


def test_validate_runem_file_valid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """No exception when `validate_yaml` returns ∅ errors."""
    cfg_path = tmp_path / "dummy.yml"
    cfg_path.touch()

    monkeypatch.setattr(uut, "_load_runem_schema", object, raising=True)
    monkeypatch.setattr(uut, "validate_yaml", lambda *_: [])

    # should run cleanly
    uut.validate_runem_file(cfg_path, all_config={})


def test_validate_runem_file_invalid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Logs every error then raises `SystemExit`."""
    cfg_path = tmp_path / "bad.yml"
    cfg_path.touch()

    logged: list[str] = []
    errors: list[str] = []

    monkeypatch.setattr(uut, "_load_runem_schema", object, raising=True)
    monkeypatch.setattr(
        uut,
        "validate_yaml",
        lambda *_: [
            _DummyErr(path=["options", 0, "type"], message="unknown field"),
            _DummyErr(path=[], message="root issue"),
        ],
    )
    monkeypatch.setattr(uut, "error", lambda msg: errors.append(str(msg)))
    monkeypatch.setattr(uut, "log", lambda msg: logged.append(str(msg)))

    with pytest.raises(SystemExit):
        uut.validate_runem_file(cfg_path, all_config={})

    # one high‑level error + per‑item log entries
    assert errors[0].startswith("failed to validate runem config")
    assert len(logged) == 2
