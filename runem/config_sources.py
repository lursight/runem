"""Source-aware values used while loading Runem configuration."""

import pathlib
import typing
from dataclasses import dataclass

from runem.types.runem_config import Config, ConfigNodes


@dataclass(frozen=True)
class ConfigSource:
    """A config file and the complete chain used to reach it."""

    path: pathlib.Path
    import_chain: typing.Tuple[pathlib.Path, ...]

    @classmethod
    def root(cls, config_path: pathlib.Path) -> "ConfigSource":
        """Create the source identity for a directly loaded config file."""
        canonical_path = config_path.resolve()
        return cls(path=canonical_path, import_chain=(canonical_path,))


@dataclass(frozen=True)
class ConfigEntry:
    """A config node paired with the file that declared it."""

    node: ConfigNodes
    source: ConfigSource


@dataclass(frozen=True)
class LoadedConfig:
    """An ordered config whose entries retain their declaring sources."""

    entries: typing.Tuple[ConfigEntry, ...]

    @classmethod
    def from_root(cls, config: Config, config_path: pathlib.Path) -> "LoadedConfig":
        """Attach one root source to an existing non-importing config."""
        source = ConfigSource.root(config_path)
        return cls(tuple(ConfigEntry(node=node, source=source) for node in config))

    def as_config(self) -> Config:
        """Return the existing public, source-free config representation."""
        return [entry.node for entry in self.entries]

    def sources(self) -> typing.Tuple[ConfigSource, ...]:
        """Return distinct sources in first-seen expansion order."""
        return tuple(dict.fromkeys(entry.source for entry in self.entries))
