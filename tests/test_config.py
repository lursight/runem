import os
import pathlib

import yaml

from runem.config import load_config
from runem.types import Config, GlobalSerialisedConfig


def test_load_config(tmp_path: pathlib.Path) -> None:
    global_config: GlobalSerialisedConfig = {
        "config": {
            "phases": ("mock phase",),
            "files": [],
            "options": [],
        }
    }
    empty_config: Config = [
        global_config,
    ]
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(yaml.dump_all(empty_config))

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    config_read_path: pathlib.Path
    loaded_config, config_read_path = load_config()
    assert loaded_config == {
        "config": {"files": [], "options": [], "phases": ("mock phase",)}
    }
    assert config_read_path == config_gen_path
