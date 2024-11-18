import io
import os
import pathlib
import typing
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from runem.config import _find_local_configs, load_project_config, load_user_configs
from runem.types.runem_config import Config, GlobalConfig


def test_load_project_config(tmp_path: pathlib.Path) -> None:
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
    loaded_config, config_read_path = load_project_config()
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


def test_load_project_config_with_no_phases(tmp_path: pathlib.Path) -> None:
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
    loaded_config, config_read_path = load_project_config()
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


def test_load_project_config_with_min_version(tmp_path: pathlib.Path) -> None:
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
            load_project_config()
        runem_stdout: str = buf.getvalue()
        assert (
            "runem: .runem.yml config requires runem '9999.99999.9999', you have"
            in runem_stdout
        )


def test_load_project_config_with_global_last(tmp_path: pathlib.Path) -> None:
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
    loaded_config, config_read_path = load_project_config()
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


@patch(
    "runem.config._find_config_file",
    return_value=(pathlib.Path("dummy path"), None),
)
@patch("pathlib.Path.exists", return_value=True)
def test_find_local_configs(
    path_exists_mock: Mock,
    find_config_file_mock: Mock,
) -> None:
    configs: typing.List[pathlib.Path] = _find_local_configs()
    assert len(configs) == 3
    assert configs == [
        pathlib.Path("dummy path"),
        pathlib.Path("dummy path"),
        pathlib.Path("~/.runem.user.yml"),
    ]
    find_config_file_mock.assert_called()
    path_exists_mock.assert_called()


@patch(
    "runem.config._find_config_file",
    return_value=(None, None),
)
@patch("pathlib.Path.exists", return_value=False)
def test_find_local_configs_finds_nothing(
    path_exists_mock: Mock,
    find_config_file_mock: Mock,
) -> None:
    configs: typing.List[pathlib.Path] = _find_local_configs()
    assert len(configs) == 0
    assert not configs
    find_config_file_mock.assert_called()
    path_exists_mock.assert_called()


@patch(
    "runem.config.load_and_parse_config",
    return_value="DUMMY CONFIG",
)
@patch(
    "runem.config._find_config_file",
    return_value=(pathlib.Path("dummy path"), None),
)
@patch("pathlib.Path.exists", return_value=True)
def test_load_user_configs(
    path_exists_mock: Mock,
    find_config_file_mock: Mock,
    load_and_parse_config_mock: Mock,
) -> None:
    configs: typing.List[typing.Tuple[Config, pathlib.Path]] = load_user_configs()
    assert len(configs) == 3
    expected_config: typing.List[typing.Tuple[Config, pathlib.Path]] = [
        ("DUMMY CONFIG", pathlib.Path("dummy path")),  # type:ignore
        ("DUMMY CONFIG", pathlib.Path("dummy path")),  # type:ignore
        ("DUMMY CONFIG", pathlib.Path("~/.runem.user.yml")),  # type:ignore
    ]
    assert configs == expected_config
    find_config_file_mock.assert_called()
    path_exists_mock.assert_called()
    load_and_parse_config_mock.assert_called()
