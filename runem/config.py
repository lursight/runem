import pathlib
import sys
import typing

import yaml

from runem.log import log
from runem.types import Config

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


def load_config() -> typing.Tuple[Config, pathlib.Path]:
    """Finds and loads the .runem.yml file."""
    cfg_filepath: pathlib.Path = _find_cfg()
    with cfg_filepath.open("r+", encoding="utf-8") as config_file_handle:
        all_config = yaml.full_load(config_file_handle)
    return all_config, cfg_filepath
