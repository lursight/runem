"""tests/test_yaml_validation.py

Unit‑tests for `runem.yaml_validation.validate_yaml`.
"""

from __future__ import annotations

from typing import Any, List

import pytest

import runem.yaml_validation as uut  # unit under test

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


class _DummyErr:  # pylint: disable=too-few-public-methods
    """Lite stand‑in for jsonschema.ValidationError."""

    def __init__(self, path: List[str]) -> None:
        self.path = path
        self.message = "boom"


class _FakeValidator:  # pylint: disable=too-few-public-methods
    """Replaces Draft202012Validator inside the UUT."""

    def __init__(self, errors: List[_DummyErr]) -> None:
        self._errors = errors

    def iter_errors(self, _instance: Any) -> List[_DummyErr]:
        return self._errors


# ──────────────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────────────


def test_validate_yaml_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returns empty list when validator reports no errors."""
    monkeypatch.setattr(
        uut,
        "Draft202012Validator",
        lambda _schema: _FakeValidator([]),
    )

    result = uut.validate_yaml({"k": "v"}, schema={})
    assert result == []


def test_validate_yaml_two_errors_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    """≥2 errors are returned in path‑sorted order."""
    errs = [_DummyErr(["z"]), _DummyErr(["a"])]  # unsorted on purpose
    monkeypatch.setattr(
        uut,
        "Draft202012Validator",
        lambda _schema: _FakeValidator(errs),
    )

    result = uut.validate_yaml({"x": 1}, schema={})

    assert [e.path for e in result] == [["a"], ["z"]]
    assert len(result) == 2
