import io
import os
import pathlib
from contextlib import redirect_stdout

import pytest

from runem.config import load_config
from runem.types import Config, GlobalConfig


def test_load_config(tmp_path: pathlib.Path) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        "- config:\n"
        "    phases:\n"
        "      - mock phase\n"
        "    min_version: 0.0.0\n"
        "    files:\n"
        "    options:\n"
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    config_read_path: pathlib.Path
    loaded_config, config_read_path = load_config()
    expected_config: Config = [
        {
            "config": {
                "files": None,
                "options": None,
                "phases": ("mock phase",),
                "min_version": "0.0.0",
            }
        }
    ]
    assert loaded_config == expected_config
    assert config_read_path == config_gen_path


def test_load_config_with_no_phases(tmp_path: pathlib.Path) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        (
            "- config:\n"  # ln 1
            "    files:\n"  # ln 2
            "    options:\n"  # ln 3
        )
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    config_read_path: pathlib.Path
    loaded_config, config_read_path = load_config()
    expected_config: Config = [
        {
            "config": {  # type: ignore # intentionally testing for missing 'phases'
                "files": None,
                "options": None,
            }
        }
    ]
    assert loaded_config == expected_config
    assert config_read_path == config_gen_path


def test_load_config_with_min_version(tmp_path: pathlib.Path) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        (
            "- config:\n"  # ln 1
            "    files:\n"  # ln 2
            "    options:\n"  # ln 3
            "    min_version: 9999.99999.9999"  # a large min-version
        )
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    with io.StringIO() as buf, redirect_stdout(buf):
        with pytest.raises(SystemExit):
            load_config()
        runem_stdout: str = buf.getvalue()
        assert (
            "runem: .runem.yml config requires runem '9999.99999.9999', you have"
            in runem_stdout
        )


def test_load_config_with_global_last(tmp_path: pathlib.Path) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        (
            "- job:\n"  # some job
            "    addr:\n"
            "      file: scripts/test_hooks/py.py\n"
            "      function: _job_py_pytest\n"
            "    label: pytest\n"
            "    when:\n"
            "      phase: analysis\n"
            "      tags:\n"
            "        - py\n"
            "        - unit test\n"
            "        - test\n"
            "- config:\n"  # the global config last
            "    files:\n"
            "    options:\n"
        )
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    config_read_path: pathlib.Path
    loaded_config, config_read_path = load_config()
    global_config: GlobalConfig = {  # type: ignore # intentionally testing for missing 'phases'
        "files": None,
        "options": None,
    }
    expected_config: Config = [
        {
            "job": {
                "addr": {
                    "file": "scripts/test_hooks/py.py",
                    "function": "_job_py_pytest",
                },
                "label": "pytest",
                "when": {
                    "phase": "analysis",
                    "tags": ["py", "unit test", "test"],  # type: ignore
                },
            }
        },
        {
            "config": global_config,
        },
    ]
    assert loaded_config == expected_config
    assert config_read_path == config_gen_path
