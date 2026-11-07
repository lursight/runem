import pytest

import runem.config.store.load_runem_schema as uut


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

    assert uut.load_runem_schema() is sentinel  # pyright: ignore [private‑access]


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
        uut.load_runem_schema()

    assert calls and "schema file not found" in calls[0]
