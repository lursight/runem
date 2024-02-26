import pathlib
import sys
import typing

import yaml
from packaging.version import Version

from runem.log import log
from runem.runem_version import get_runem_version
from runem.types import Config, GlobalConfig, GlobalSerialisedConfig

CFG_FILE_YAML = pathlib.Path(".runem.yml")


def _search_up_dirs_for_file(
    start_dir: pathlib.Path, search_filename: typing.Union[str, pathlib.Path]
) -> typing.Optional[pathlib.Path]:
    """Search 'up' from start_dir looking for search_filename."""
    while 1:
        cfg_candidate = start_dir / search_filename
        if cfg_candidate.exists():
            return cfg_candidate
        exhausted_stack: bool = start_dir == start_dir.parent
        if exhausted_stack:
            return None
        start_dir = start_dir.parent


def _search_up_multiple_dirs_for_file(
    start_dirs: typing.Iterable[pathlib.Path],
    search_filename: typing.Union[str, pathlib.Path],
) -> typing.Optional[pathlib.Path]:
    """Same as _search_up_dirs_for_file() but for multiple dir start points."""
    for start_dir in start_dirs:
        found: typing.Optional[pathlib.Path] = _search_up_dirs_for_file(
            start_dir, search_filename
        )
        if found is not None:
            return found
    return None


def _find_cfg() -> pathlib.Path:
    """Searches up from the cwd for a .runem.yml config file."""
    start_dirs = (pathlib.Path(".").absolute(),)
    cfg_candidate: typing.Optional[pathlib.Path] = _search_up_multiple_dirs_for_file(
        start_dirs, CFG_FILE_YAML
    )
    if cfg_candidate:
        return cfg_candidate

    # error out and exit as we currently require the cfg file as it lists jobs.
    log(f"ERROR: Config not found! Looked from {start_dirs}")
    sys.exit(1)


def _conform_global_config_types(
    all_config: Config,
) -> typing.Tuple[Config, typing.Optional[GlobalConfig]]:
    """Ensure that the types match the type-spec."""
    assert isinstance(all_config, list)
    # NOTE: A note of performance. This extra loop over the config should have
    #       minimal impact as the global config should _normally_ be first in
    #       the file.
    global_config: typing.Optional[GlobalConfig] = None
    for idx, config in enumerate(all_config):
        # Notice the 'continue' statement.
        g_config: GlobalSerialisedConfig = config  # type: ignore
        if "config" not in g_config:
            # keep searching
            continue
        global_config = g_config["config"]
        if "phases" in global_config:
            all_config[idx]["config"]["phases"] = tuple(  # type: ignore
                global_config["phases"]
            )
    return all_config, global_config


def load_config() -> typing.Tuple[Config, pathlib.Path]:
    """Finds and loads the .runem.yml file."""
    cfg_filepath: pathlib.Path = _find_cfg()
    with cfg_filepath.open("r+", encoding="utf-8") as config_file_handle:
        all_config = yaml.full_load(config_file_handle)

    conformed_config: Config
    global_config: typing.Optional[GlobalConfig]
    conformed_config, global_config = _conform_global_config_types(all_config)

    # is the config pinned to a version of runem?
    if (
        global_config is not None
        and ("min_version" in global_config)
        and (global_config["min_version"] is not None)
    ):
        # check that the version of runem is supported by the config file
        runem_version = get_runem_version()
        min_required_version: Version = Version(global_config["min_version"].strip())
        if min_required_version > runem_version:
            log(
                (
                    f".runem.yml config requires runem '{min_required_version}', "
                    f"you have '{runem_version}'. You need to update runem."
                )
            )
            sys.exit(1)

    return conformed_config, cfg_filepath
