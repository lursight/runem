"""Source-aware loading for local Runem configuration."""

import copy
import pathlib
import typing
from dataclasses import dataclass, field

import yaml
from typing_extensions import TypeGuard

from runem.config_validate import validate_runem_file
from runem.job import Job
from runem.types.runem_config import (
    Config,
    ConfigDocument,
    ConfigDocumentNode,
    ConfigNodes,
    HookSerialisedConfig,
    ImportSerialisedConfig,
    JobSerialisedConfig,
    JobWrapper,
)
from runem.yaml_utils import load_yaml_object

MAX_CONFIG_IMPORT_DEPTH = 50
ConfigImportStack = typing.Tuple[pathlib.Path, ...]


class ConfigImportError(ValueError):
    """A config import failure with stable machine-readable context."""

    def __init__(
        self,
        code: str,
        message: str,
        source_path: pathlib.Path,
        import_chain: ConfigImportStack,
        requested_path: typing.Optional[str] = None,
    ) -> None:
        chain_text = " -> ".join(str(path) for path in import_chain)
        super().__init__(f"{message}; import chain: {chain_text}")
        self.code = code
        self.source_path = source_path
        self.import_chain = import_chain
        self.requested_path = requested_path


@dataclass(frozen=True)
class ConfigSource:
    """A config file and the complete chain used to reach it."""

    path: pathlib.Path
    import_chain: ConfigImportStack = field(compare=False)

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
class ConfigImportEdge:
    """One directed edge in the expanded config import graph."""

    importing_source: ConfigSource
    imported_source: ConfigSource
    requested_path: str


@dataclass(frozen=True)
class LoadedConfig:
    """An ordered config whose entries retain their declaring sources."""

    entries: typing.Tuple[ConfigEntry, ...]
    all_sources: typing.Tuple[ConfigSource, ...]
    import_edges: typing.Tuple[ConfigImportEdge, ...] = ()

    @classmethod
    def from_root(cls, config: Config, config_path: pathlib.Path) -> "LoadedConfig":
        """Attach one root source to an existing non-importing config."""
        source = ConfigSource.root(config_path)
        entries = tuple(ConfigEntry(node=node, source=source) for node in config)
        return cls(entries=entries, all_sources=(source,))

    def as_config(self) -> Config:
        """Return the existing public, source-free config representation."""
        return [entry.node for entry in self.entries]

    def sources(self) -> typing.Tuple[ConfigSource, ...]:
        """Return distinct sources in first-seen expansion order."""
        return tuple(dict.fromkeys(self.all_sources))


def _resolve_import_path(
    root_dir: pathlib.Path,
    source: ConfigSource,
    requested_path: str,
) -> pathlib.Path:
    """Resolve one local import while enforcing its root boundary."""
    import_path = pathlib.Path(requested_path)
    if import_path.is_absolute():
        raise ConfigImportError(
            code="absolute_import",
            message=(
                f"Invalid import in '{source.path}': absolute path "
                f"'{requested_path}' is not allowed"
            ),
            source_path=source.path,
            import_chain=source.import_chain,
            requested_path=requested_path,
        )

    resolved_path = (root_dir / import_path).resolve()
    try:
        resolved_path.relative_to(root_dir)
    except ValueError as err:
        raise ConfigImportError(
            code="import_outside_root",
            message=(
                f"Invalid import in '{source.path}': path '{requested_path}' "
                "escapes the root config directory"
            ),
            source_path=source.path,
            import_chain=source.import_chain,
            requested_path=requested_path,
        ) from err

    if not resolved_path.is_file():
        raise ConfigImportError(
            code="import_not_file",
            message=(
                f"Unable to import '{requested_path}' from '{source.path}': "
                "target does not exist or is not a regular file"
            ),
            source_path=source.path,
            import_chain=source.import_chain,
            requested_path=requested_path,
        )
    return resolved_path


def _validate_config_document(
    value: object,
    source: ConfigSource,
) -> TypeGuard[ConfigDocument]:
    """Validate and narrow a YAML value to the schema's document type."""
    validate_runem_file(source.path, value)
    return True


def _load_yaml_config(source: ConfigSource) -> ConfigDocument:
    """Read and structurally validate one source document."""
    try:
        loaded: object = load_yaml_object(source.path)
    except (OSError, yaml.YAMLError) as err:
        raise ConfigImportError(
            code="config_load_failed",
            message=f"Unable to load config '{source.path}': {err}",
            source_path=source.path,
            import_chain=source.import_chain,
        ) from err

    if _validate_config_document(loaded, source):
        return loaded
    raise AssertionError("Config validation returned without a result")


def _is_import_node(
    node: ConfigDocumentNode,
) -> TypeGuard[ImportSerialisedConfig]:
    """Return whether a document node is an import directive."""
    return "import" in node


def _is_config_node(node: ConfigDocumentNode) -> TypeGuard[ConfigNodes]:
    """Return whether a document node belongs in the expanded public config."""
    return "import" not in node


def _is_job_node(node: ConfigNodes) -> TypeGuard[JobSerialisedConfig]:
    """Return whether an expanded node contains a job."""
    return "job" in node


def _is_hook_node(node: ConfigNodes) -> TypeGuard[HookSerialisedConfig]:
    """Return whether an expanded node contains a hook."""
    return "hook" in node


def _callable_wrapper(node: ConfigNodes) -> typing.Optional[JobWrapper]:
    """Return the callable wrapper owned by a job or hook node."""
    if _is_job_node(node):
        return node["job"]
    if _is_hook_node(node):
        return node["hook"]
    return None


def _create_imported_source(
    root_dir: pathlib.Path,
    source: ConfigSource,
    requested_path: str,
) -> ConfigSource:
    """Create the child source after checking depth, containment, and cycles."""
    if len(source.import_chain) - 1 >= MAX_CONFIG_IMPORT_DEPTH:
        raise ConfigImportError(
            code="import_too_deep",
            message=(
                f"Config import depth exceeds {MAX_CONFIG_IMPORT_DEPTH} while "
                f"importing '{requested_path}' from '{source.path}'"
            ),
            source_path=source.path,
            import_chain=source.import_chain,
            requested_path=requested_path,
        )

    imported_path = _resolve_import_path(root_dir, source, requested_path)
    imported_chain = (*source.import_chain, imported_path)
    if imported_path in source.import_chain:
        raise ConfigImportError(
            code="import_cycle",
            message=f"Config import cycle detected at '{imported_path}'",
            source_path=source.path,
            import_chain=imported_chain,
            requested_path=requested_path,
        )
    return ConfigSource(path=imported_path, import_chain=imported_chain)


def _normalise_imported_address(
    root_dir: pathlib.Path,
    entry: ConfigEntry,
) -> ConfigEntry:
    """Rebase an imported file-addressed callable to the root config directory."""
    if len(entry.source.import_chain) == 1:
        return entry

    node = entry.node
    wrapper = _callable_wrapper(node)
    if wrapper is None or "addr" not in wrapper:
        return entry

    requested_path = wrapper["addr"]["file"]
    address_path = pathlib.Path(requested_path)
    if not address_path.is_absolute():
        address_path = entry.source.path.parent / address_path
    canonical_path = address_path.resolve()
    try:
        root_relative_path = canonical_path.relative_to(root_dir)
    except ValueError as err:
        raise ConfigImportError(
            code="address_outside_root",
            message=(
                f"Python address '{requested_path}' in '{entry.source.path}' "
                "escapes the root config directory"
            ),
            source_path=entry.source.path,
            import_chain=entry.source.import_chain,
            requested_path=requested_path,
        ) from err

    if not canonical_path.is_file():
        raise ConfigImportError(
            code="address_not_file",
            message=(
                f"Python address '{requested_path}' in '{entry.source.path}' "
                "does not exist or is not a regular file"
            ),
            source_path=entry.source.path,
            import_chain=entry.source.import_chain,
            requested_path=requested_path,
        )

    normalised_node = copy.deepcopy(node)
    if _is_job_node(normalised_node):
        normalised_node["job"]["addr"]["file"] = str(root_relative_path)
    if _is_hook_node(normalised_node):
        normalised_node["hook"]["addr"]["file"] = str(root_relative_path)
    return ConfigEntry(node=normalised_node, source=entry.source)


def _expand_source(
    root_dir: pathlib.Path,
    source: ConfigSource,
) -> LoadedConfig:
    """Expand one source and all of its imports depth-first."""
    entries: typing.List[ConfigEntry] = []
    all_sources: typing.List[ConfigSource] = [source]
    import_edges: typing.List[ConfigImportEdge] = []
    for node in _load_yaml_config(source):
        if _is_config_node(node):
            entry = ConfigEntry(node=node, source=source)
            entries.append(_normalise_imported_address(root_dir, entry))
            continue

        if not _is_import_node(node):
            raise AssertionError("Validated config node has no recognised type")
        requested_path = node["import"]
        imported_source = _create_imported_source(root_dir, source, requested_path)
        imported_config = _expand_source(root_dir, imported_source)
        entries.extend(imported_config.entries)
        all_sources.extend(imported_config.all_sources)
        import_edges.append(
            ConfigImportEdge(
                importing_source=source,
                imported_source=imported_source,
                requested_path=requested_path,
            )
        )
        import_edges.extend(imported_config.import_edges)
    return LoadedConfig(
        entries=tuple(entries),
        all_sources=tuple(all_sources),
        import_edges=tuple(import_edges),
    )


def load_config_with_sources(config_path: pathlib.Path) -> LoadedConfig:
    """Load and expand one local config graph with source context."""
    root_source = ConfigSource.root(config_path)
    return _expand_source(root_source.path.parent, root_source)


def validate_imported_config_conflicts(loaded_config: LoadedConfig) -> None:
    """Report cross-source global and job conflicts with both source files."""
    if not loaded_config.import_edges:
        return

    first_global_source: typing.Optional[ConfigSource] = None
    job_sources: typing.Dict[str, ConfigSource] = {}
    for entry in loaded_config.entries:
        if "config" in entry.node:
            if first_global_source is not None:
                raise ConfigImportError(
                    code="duplicate_global_config",
                    message=(
                        "Found multiple global config entries in "
                        f"'{first_global_source.path}' and '{entry.source.path}'"
                    ),
                    source_path=entry.source.path,
                    import_chain=entry.source.import_chain,
                )
            first_global_source = entry.source
            continue

        job = entry.node.get("job")
        if not isinstance(job, typing.Mapping):
            continue
        job_name = Job.get_job_name(job)
        first_job_source = job_sources.get(job_name)
        if first_job_source is not None:
            raise ConfigImportError(
                code="duplicate_job",
                message=(
                    f"Job '{job_name}' is declared in both "
                    f"'{first_job_source.path}' and '{entry.source.path}'"
                ),
                source_path=entry.source.path,
                import_chain=entry.source.import_chain,
            )
        job_sources[job_name] = entry.source
