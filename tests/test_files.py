import pathlib
from argparse import Namespace
from collections import defaultdict
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from runem.config_metadata import ConfigMetadata
from runem.files import find_files
from runem.informative_dict import InformativeDict
from runem.types.filters import FilePathListLookup


def _prep_config(
    tmp_path: pathlib.Path,
    check_modified_files: bool,
    check_head_files: bool,
    always_files: Optional[List[str]],
    git_since_branch: Optional[str],
) -> ConfigMetadata:
    config_metadata: ConfigMetadata = ConfigMetadata(
        cfg_filepath=tmp_path / ".runem.yml.no-exist",  # only the path is used
        phases=("dummy phase 1",),
        options_config=tuple(),
        file_filters={
            "dummy tag": {
                "tag": "dummy tag",
                "regex": ".*1.txt",  # should match just one file
            }
        },
        hook_manager=MagicMock(),
        jobs=defaultdict(list),
        all_job_names=set(),
        all_job_phases=set(),
        all_job_tags=set(),
    )
    config_metadata.set_cli_data(
        args=Namespace(
            check_modified_files=check_modified_files,
            check_head_files=check_head_files,
            always_files=always_files,
            git_since_branch=git_since_branch,
        ),
        jobs_to_run=set(),  # JobNames,
        phases_to_run=set(),  # JobPhases,
        tags_to_run=set(),  # ignored JobTags,
        tags_to_avoid=set(),  # ignored  JobTags,
        options=InformativeDict({}),  # Options,
    )

    return config_metadata


@pytest.mark.parametrize(
    "check_head_files",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "check_modified_files",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "always_files",
    [
        ["1.always", "2.no_exist.always", "3.always"],
        [],  # empty array
        None,  # trigger defaults
    ],
)
@patch(
    "runem.files.subprocess_check_output",
)
def test_find_files_basic(
    mock_subprocess_check_output: Mock,
    always_files: Optional[List[str]],
    check_modified_files: bool,
    check_head_files: bool,
    tmp_path: pathlib.Path,
) -> None:
    file_strings: List[str] = []
    for file_str in ("test_file_1.txt", "test_file_2.txt"):
        test_file: pathlib.Path = tmp_path / file_str
        test_file.touch()  # write some empty string aka 'touch' the file
        file_strings.append(str(test_file))
    mock_subprocess_check_output.return_value = str.encode("\n".join(file_strings))

    created_always_files: Optional[List[str]] = None
    if always_files is not None:
        created_always_files = []
        for always_file in always_files:
            file_path: pathlib.Path = tmp_path / always_file
            if "no_exist" not in always_file:
                # only create files if they are NOT tagged with 'no_exist'
                file_path.touch()
            created_always_files.append(str(file_path))

    config_metadata = _prep_config(
        tmp_path,
        check_modified_files=check_modified_files,
        check_head_files=check_head_files,
        always_files=created_always_files,
        git_since_branch=None,
    )
    results: FilePathListLookup = find_files(config_metadata)
    if check_modified_files and check_head_files:
        assert (
            mock_subprocess_check_output.call_count == 3
        ), "twice for modified, once for head"
        assert results == {
            "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
        }
    elif check_modified_files:
        assert mock_subprocess_check_output.call_count == 2, "twice for modified"
        assert results == {
            "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
        }
    else:
        assert mock_subprocess_check_output.call_count == 1, "once for git ls-files"
        assert results == {
            "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
        }


@pytest.mark.parametrize(
    "git_since_branch",
    [
        None,
        "/dummy/branch/name",
    ],
)
@patch(
    "runem.files.subprocess_check_output",
)
def test_find_files_git_since_branch(
    mock_subprocess_check_output: Mock,
    git_since_branch: Optional[str],
    tmp_path: pathlib.Path,
) -> None:
    file_strings: List[str] = []
    for file_str in ("test_file_1.txt", "test_file_2.txt"):
        test_file: pathlib.Path = tmp_path / file_str
        test_file.touch()  # write some empty string aka 'touch' the file
        file_strings.append(str(test_file))
    mock_subprocess_check_output.return_value = str.encode("\n".join(file_strings))

    config_metadata = _prep_config(
        tmp_path,
        check_modified_files=False,
        check_head_files=False,
        always_files=None,
        git_since_branch=git_since_branch,
    )
    results: FilePathListLookup = find_files(config_metadata)
    if git_since_branch is None:
        assert mock_subprocess_check_output.call_count == 1, "once for git ls-files"
        assert results == {
            "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
        }
    else:
        assert mock_subprocess_check_output.call_count == 1, "once for git ls-files"
        assert results == {
            "dummy tag": [file_strings[0]]  # we filter in only the *1* files.
        }
