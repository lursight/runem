import io
import os
import pathlib
import typing
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Self
from unittest.mock import Mock, patch

import pytest

from runem.config.config import (
    CfgCandidate,
    _find_local_configs,
    _load_and_parse_config_with_sources,
    _search_up_dirs_for_file,
    _search_up_multiple_dirs_for_file,
    load_and_parse_config,
    load_project_config,
    load_user_configs,
)
from runem.types.runem_config import Config, GlobalConfig

# pylint: disable=protected-access


@patch(
    "runem.config.config._find_config_file",
)
def test_load_project_config(
    find_config_file_mock: Mock,
    tmp_path: pathlib.Path,
) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        "- config:\n"
        "    phases:\n"
        "      - mock phase\n"
        "    min_version: 0.0.0\n"
        "    files:\n"
        "    options:\n"
    )
    find_config_file_mock.return_value = CfgCandidate(
        file=config_gen_path, start_dirs=tuple()
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    loaded_config = load_project_config()
    find_config_file_mock.assert_called_once()
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


@patch(
    "runem.config.config._find_config_file",
)
def test_load_project_config_with_no_phases(
    find_config_file_mock: Mock,
    tmp_path: pathlib.Path,
) -> None:
    config_gen_path: pathlib.Path = tmp_path / ".runem.yml"
    config_gen_path.write_text(
        (
            "- config:\n"  # ln 1
            "    files:\n"  # ln 2
            "    options:\n"  # ln 3
        )
    )
    find_config_file_mock.return_value = CfgCandidate(
        file=config_gen_path, start_dirs=(config_gen_path.parent,)
    )

    # set the working dir to where the config is
    os.chdir(tmp_path)

    loaded_config: Config
    loaded_config = load_project_config()
    find_config_file_mock.assert_called_once()
    expected_config: Config = [
        {
            "config": {  # type: ignore # intentionally testing for missing 'phases'
                "files": None,
                "options": None,
            }
        }
    ]
    assert loaded_config == expected_config


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
            load_and_parse_config(config_gen_path)
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
    loaded_config = load_and_parse_config(config_gen_path)
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


def test_load_config_with_sources_preserves_public_config(
    tmp_path: pathlib.Path,
) -> None:
    config_path = tmp_path / ".runem.yml"
    config_path.write_text("- job:\n    command: test\n    label: test\n")

    loaded = _load_and_parse_config_with_sources(config_path)

    assert loaded.as_config() == [{"job": {"command": "test", "label": "test"}}]
    assert loaded.entries[0].source.path == config_path.resolve()


@patch(
    "runem.config.config._find_config_file",
    return_value=CfgCandidate(file=pathlib.Path("dummy path"), start_dirs=tuple()),
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
    "runem.config.config._find_config_file",
    return_value=CfgCandidate(file=None, start_dirs=tuple()),
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
    "runem.config.config.load_and_parse_config",
    return_value="DUMMY CONFIG",
)
@patch(
    "runem.config.config._find_config_file",
    return_value=CfgCandidate(
        file=pathlib.Path("dummy path"),
        start_dirs=tuple(),
    ),
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


@dataclass(slots=True)
class MockPath:
    """Mock a filesystem path with sequential exists() responses."""

    path: pathlib.PurePath
    exists_results: list[bool]

    @property
    def parent(self) -> Self:
        """Return the parent, sharing the response list."""
        return type(self)(self.path.parent, self.exists_results)

    def __truediv__(self, part: str | pathlib.PurePath) -> Self:
        """Join a path, sharing the response list."""
        return type(self)(self.path / part, self.exists_results)

    def exists(self) -> bool:
        """Consume the next mocked existence result."""
        return self.exists_results.pop(0)

    def __fspath__(self) -> str:  # pragma: no cover
        """Return the underlying filesystem path.

        cspell: words fspath
        """
        return str(self.path)


def test_search_up_dirs_for_file() -> None:
    search_file: str = "file.to.find"
    start_dir = MockPath(
        path=pathlib.PurePath("contains/empty"),
        exists_results=[
            False,  # <- `contains/empty/file.to.find`
            True,  # <- `contains/file.to.find`
        ],
    )
    res: typing.Optional[pathlib.Path] = _search_up_dirs_for_file(
        start_dir,  # type:ignore
        search_filename=search_file,
    )
    assert res.path == pathlib.Path(f"contains/{search_file}")  # type: ignore
    assert len(start_dir.exists_results) == 0


def test_search_up_multiple_dirs_for_file() -> None:
    search_file: str = "file.to.find"
    start_dir_1 = MockPath(
        path=pathlib.PurePath("contains/empty"),
        exists_results=[
            False,  # <- `contains/empty/file.to.find`
            True,  # <- `contains/file.to.find`
        ],
    )
    start_dir_2 = MockPath(
        path=pathlib.PurePath("alt/empty"),
        exists_results=[False, False],
    )
    res: typing.Optional[pathlib.Path] = _search_up_multiple_dirs_for_file(
        (start_dir_1, start_dir_2),  # type:ignore
        search_filename=search_file,
    )
    assert res.path == pathlib.Path(f"contains/{search_file}")  # type: ignore
    assert len(start_dir_1.exists_results) == 0
