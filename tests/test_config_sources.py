"""Tests for source-aware config loading values."""

import pathlib

from runem.config_sources import ConfigEntry, ConfigSource, LoadedConfig
from runem.types.runem_config import Config


def test_config_source_root_uses_one_canonical_path(tmp_path: pathlib.Path) -> None:
    config_path = tmp_path / "nested" / ".." / ".runem.yml"

    source = ConfigSource.root(config_path)

    assert source.path == (tmp_path / ".runem.yml").resolve()
    assert source.import_chain == (source.path,)


def test_loaded_config_preserves_entries_and_public_shape(
    tmp_path: pathlib.Path,
) -> None:
    config: Config = [
        {"job": {"command": "first", "label": "first"}},
        {"job": {"command": "second", "label": "second"}},
    ]

    loaded = LoadedConfig.from_root(config, tmp_path / ".runem.yml")

    assert loaded.as_config() == config
    assert [entry.node for entry in loaded.entries] == config
    assert loaded.sources() == (loaded.entries[0].source,)


def test_loaded_config_sources_follow_first_seen_order(
    tmp_path: pathlib.Path,
) -> None:
    root_source = ConfigSource.root(tmp_path / ".runem.yml")
    imported_source = ConfigSource(
        path=(tmp_path / "imported.yml").resolve(),
        import_chain=(root_source.path, (tmp_path / "imported.yml").resolve()),
    )
    first_node: Config = [{"job": {"command": "first", "label": "first"}}]
    second_node: Config = [{"job": {"command": "second", "label": "second"}}]
    loaded = LoadedConfig(
        entries=(
            ConfigEntry(first_node[0], root_source),
            ConfigEntry(second_node[0], imported_source),
            ConfigEntry(first_node[0], root_source),
        ),
        all_sources=(root_source, imported_source, root_source),
    )

    assert loaded.sources() == (root_source, imported_source)
